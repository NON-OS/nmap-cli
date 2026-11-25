"""Lingua: si parte in italiano, inglese e cinese su richiesta, e tutto l'output cambia."""

from __future__ import annotations

import io
import os
import string
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from nmapcli import cli, i18n, profiles

SCOPE = """
[engagement]
nome = "PROVA"
autorizzato_da = "Mario Bianchi, CISO"
riferimento = "PROVA-1"
valido_dal = 2026-01-01
valido_fino = 2099-12-31

[scope]
include = ["192.0.2.0/25"]
"""

XML_VECCHIO = """<nmaprun args="nmap -sV x" startstr="">
<host><status state="up"/><address addr="10.0.0.5" addrtype="ipv4"/>
<ports><port protocol="tcp" portid="22"><state state="open"/><service name="ssh" product="OpenSSH" version="9.2"/></port>
<port protocol="tcp" portid="80"><state state="open"/><service name="http"/></port></ports></host>
<host><status state="up"/><address addr="10.0.0.7" addrtype="ipv4"/></host>
</nmaprun>"""

XML_NUOVO = """<nmaprun args="nmap" startstr="">
<host><status state="up"/><address addr="10.0.0.5" addrtype="ipv4"/>
<ports><port protocol="tcp" portid="22"><state state="open"/><service name="ssh" product="OpenSSH" version="9.6"/></port>
<port protocol="tcp" portid="443"><state state="open"/></port></ports></host>
<host><status state="up"/><address addr="10.0.0.9" addrtype="ipv4"/></host>
</nmaprun>"""


def _senza_nonos_lang() -> mock._patch[dict[str, str]]:
    env = {k: v for k, v in os.environ.items() if k != "NONOS_LANG"}
    return mock.patch.dict(os.environ, env, clear=True)


class TestLingua(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.TemporaryDirectory()
        self.scope = Path(self.dir.name) / "scope.toml"
        self.scope.write_text(SCOPE)
        self.vecchio = Path(self.dir.name) / "vecchia.xml"
        self.vecchio.write_text(XML_VECCHIO)
        self.nuovo = Path(self.dir.name) / "nuova.xml"
        self.nuovo.write_text(XML_NUOVO)

    def tearDown(self) -> None:
        i18n.imposta_lingua("it")
        profiles.applica_lingua("it")
        self.dir.cleanup()

    def _esegui(self, *argv: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with _senza_nonos_lang(), redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(list(argv))
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    # -- scelta della lingua ---------------------------------------------------

    def test_si_parte_in_italiano_anche_con_un_locale_inglese(self) -> None:
        with _senza_nonos_lang(), mock.patch.dict(os.environ, {"LANG": "en_US.UTF-8", "LC_ALL": "en_US.UTF-8"}):
            self.assertEqual(i18n.imposta_lingua(), "it")

    def test_nonos_lang_sceglie_la_lingua(self) -> None:
        with mock.patch.dict(os.environ, {"NONOS_LANG": "zh_CN"}):
            self.assertEqual(i18n.imposta_lingua(), "zh")

    def test_il_flag_batte_la_variabile(self) -> None:
        with mock.patch.dict(os.environ, {"NONOS_LANG": "zh"}):
            self.assertEqual(i18n.imposta_lingua("en"), "en")

    def test_lingua_sconosciuta_ripiega_sull_italiano(self) -> None:
        with _senza_nonos_lang():
            self.assertEqual(i18n.imposta_lingua("fr"), "it")

    def test_forma_con_uguale(self) -> None:
        rc, testo = self._esegui("--lang=en", "profili")
        self.assertEqual(rc, 0)
        self.assertIn("noise", testo)

    # -- catalogo ------------------------------------------------------------

    def test_ogni_messaggio_ha_tre_lingue_con_gli_stessi_campi(self) -> None:
        def campi(testo: str) -> set[str]:
            return {f for _, f, _, _ in string.Formatter().parse(testo) if f}

        for chiave, voci in i18n.MSG.items():
            self.assertEqual(set(voci), {"it", "en", "zh"}, chiave)
            for lingua in ("en", "zh"):
                self.assertEqual(campi(voci[lingua]), campi(voci["it"]), f"{chiave}/{lingua}")

    def test_ogni_profilo_ha_la_traduzione(self) -> None:
        originali = profiles._ORIGINALI[0]
        for lingua in ("en", "zh"):
            self.assertEqual(set(profiles._TR_PROFILI[lingua]), set(originali), lingua)
            for nome, (desc, quando) in profiles._TR_PROFILI[lingua].items():
                self.assertTrue(desc and quando, f"{lingua}/{nome}")

    def test_ogni_flag_vietato_ha_il_motivo_tradotto(self) -> None:
        motivi = set(profiles._ORIGINALI[1].values()) | set(profiles._ORIGINALI[2].values())
        for lingua in ("en", "zh"):
            self.assertEqual(motivi - set(profiles._TR_VIETATI[lingua]), set(), lingua)

    # -- output --------------------------------------------------------------

    def test_profili_in_tre_lingue(self) -> None:
        for lingua, parola in (("it", "rumore"), ("en", "noise"), ("zh", "噪声")):
            rc, testo = self._esegui("--lang", lingua, "profili")
            self.assertEqual(rc, 0, lingua)
            self.assertIn(parola, testo, lingua)

    def test_motivo_di_scope_tradotto(self) -> None:
        attesi = (
            ("it", "hostname non presente tra gli inclusi"),
            ("en", "hostname not among the included ones"),
            ("zh", "主机名不在包含列表中"),
        )
        for lingua, frase in attesi:
            rc, testo = self._esegui("--lang", lingua, "verifica", "altro.invalid", "--scope", str(self.scope))
            self.assertEqual(rc, 3, lingua)
            self.assertIn(frase, testo, lingua)

    def test_flag_vietato_tradotto(self) -> None:
        attesi = (
            ("it", "non è ammesso: legge target da file"),
            ("en", "is not allowed: reads targets from a file"),
            ("zh", "不被允许：从文件读取目标"),
        )
        for lingua, frase in attesi:
            argv = ["--lang", lingua, "scansiona", "rapido", "192.0.2.10", "--scope", str(self.scope), "--", "-iL", "x"]
            rc, testo = self._esegui(*argv)
            self.assertEqual(rc, 2, lingua)
            self.assertIn(frase, testo, lingua)

    def test_scansiona_tradotto(self) -> None:
        attesi = (("it", "Ingaggio :"), ("en", "Engagement:"), ("zh", "项目     :"))
        for lingua, frase in attesi:
            argv = ["--lang", lingua, "scansiona", "rapido", "192.0.2.10", "--scope", str(self.scope)]
            argv += ["--out", str(Path(self.dir.name) / "o"), "--audit", str(Path(self.dir.name) / "a.jsonl")]
            rc, testo = self._esegui(*argv)
            self.assertEqual(rc, 0, lingua)
            self.assertIn(frase, testo, lingua)
            self.assertIn("Dry-run", testo, lingua)

    def test_rapporto_e_confronta_tradotti(self) -> None:
        attesi = (
            ("it", "# Rapporto di scansione", "+ porta aperta   10.0.0.5 443/tcp"),
            ("en", "# Scan report", "+ port opened    10.0.0.5 443/tcp"),
            ("zh", "# 扫描报告", "+ 端口开放       10.0.0.5 443/tcp"),
        )
        for lingua, titolo, riga in attesi:
            rc, testo = self._esegui("--lang", lingua, "rapporto", str(self.vecchio), "--formato", "markdown")
            self.assertEqual(rc, 0, lingua)
            self.assertIn(titolo, testo, lingua)
            rc, testo = self._esegui("--lang", lingua, "confronta", str(self.vecchio), str(self.nuovo))
            self.assertEqual(rc, 0, lingua)
            self.assertIn(riga, testo, lingua)

    def test_help_tradotto_anche_nelle_parti_di_argparse(self) -> None:
        for lingua, parola in (("it", "opzioni"), ("en", "options"), ("zh", "选项")):
            rc, testo = self._esegui("--lang", lingua, "--help")
            self.assertEqual(rc, 0, lingua)
            self.assertIn(parola, testo, lingua)

    def test_si_torna_all_italiano(self) -> None:
        nome = next(iter(profiles.PROFILI))
        italiano = profiles._ORIGINALI[0][nome].descrizione
        self._esegui("--lang", "en", "profili")
        self.assertNotEqual(profiles.PROFILI[nome].descrizione, italiano)
        self._esegui("profili")
        self.assertEqual(profiles.PROFILI[nome].descrizione, italiano)
        self.assertEqual(profiles._LUNGHE, profiles._ORIGINALI[1])

    def test_modello_di_scope_nella_lingua_scelta(self) -> None:
        attesi = (("it", "Compilalo a mano"), ("en", "Fill it in by hand"), ("zh", "手工填写"))
        for lingua, frase in attesi:
            with tempfile.TemporaryDirectory() as cartella:
                nuovo = Path(cartella) / f"scope-{lingua}.toml"
                rc, _ = self._esegui("--lang", lingua, "init", str(nuovo))
                self.assertEqual(rc, 0, lingua)
                testo = nuovo.read_text()
                self.assertIn(frase, testo, lingua)
                self.assertIn("autorizzato_da =", testo, lingua)


if __name__ == "__main__":
    unittest.main()
