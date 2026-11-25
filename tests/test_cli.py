import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nmapcli import cli, errors

SCOPE = """
[engagement]
nome = "t"
autorizzato_da = "Qualcuno"
riferimento = "REF-1"
valido_dal = 2000-01-01
valido_fino = 2999-12-31

[scope]
include = ["127.0.0.0/30"]
esclude = ["127.0.0.2"]
"""


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = cli.main(list(args))
        except SystemExit as e:
            rc = e.code
    return rc, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        d = Path(self._d.name)
        self.scope = str(d / "scope.toml")
        Path(self.scope).write_text(SCOPE)
        self.audit = str(d / "a.jsonl")
        self.cwd = os.getcwd()
        os.chdir(d)
        self.addCleanup(os.chdir, self.cwd)

    def test_dry_run_di_default_e_non_crea_output(self):
        rc, out, _ = run("scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit)
        self.assertEqual(rc, errors.OK)
        self.assertIn("Dry-run", out)
        self.assertFalse(Path("out").exists())
        self.assertIn('"evento":"dry_run"', Path(self.audit).read_text())

    def test_fuori_scope_esce_con_3_e_non_logga_un_avvio(self):
        rc, _, err = run("scansiona", "rapido", "127.0.0.1", "8.8.8.8", "--scope", self.scope, "--audit", self.audit)
        self.assertEqual(rc, errors.FUORI_SCOPE)
        self.assertIn("8.8.8.8", err)
        self.assertFalse(Path(self.audit).exists())

    def test_escluso(self):
        rc, *_ = run("verifica", "127.0.0.2", "--scope", self.scope)
        self.assertEqual(rc, errors.FUORI_SCOPE)

    def test_flag_vietato_dopo_doppio_trattino(self):
        rc, _, err = run(
            "scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit, "--", "-iL", "x"
        )
        self.assertEqual(rc, errors.USO)
        self.assertIn("-iL", err)

    def test_esegui_senza_conferma_in_ambiente_non_interattivo(self):
        # un nmap finto nel PATH: il test non deve dipendere da nmap installato
        finto = Path(self._d.name) / "bin"
        finto.mkdir()
        (finto / "nmap").write_text(
            '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "Nmap version 0.0 ( https://nmap.org )"; exit 0; fi\nexit 0\n'
        )
        (finto / "nmap").chmod(0o755)
        vecchio = os.environ["PATH"]
        os.environ["PATH"] = str(finto)
        self.addCleanup(os.environ.__setitem__, "PATH", vecchio)
        rc, _, err = run("scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit, "--esegui")
        self.assertEqual(rc, errors.RIFIUTATO)
        self.assertIn('"evento":"rifiutato"', Path(self.audit).read_text())

    def test_scope_mancante(self):
        rc, *_ = run("verifica", "127.0.0.1", "--scope", "nope.toml")
        self.assertEqual(rc, errors.SCOPE_INVALIDO)

    def test_init_non_sovrascrive(self):
        self.assertEqual(run("init", "nuovo.toml")[0], errors.OK)
        self.assertEqual(run("init", "nuovo.toml")[0], errors.USO)

    def test_modello_di_init_non_autorizza_nulla_di_reale(self):
        run("init", "m.toml")
        rc, *_ = run("verifica", "8.8.8.8", "--scope", "m.toml")
        self.assertIn(rc, (errors.FUORI_SCOPE, errors.SCOPE_INVALIDO))

    def test_audit_comando(self):
        run("scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit)
        self.assertEqual(run("audit", self.audit)[0], errors.OK)

    def test_profili_elenca_tutto(self):
        rc, out, _ = run("profili")
        self.assertEqual(rc, errors.OK)
        self.assertIn("tcp-completo", out)


if __name__ == "__main__":
    unittest.main()


class SenzaBinarioTest(unittest.TestCase):
    """Il dry-run deve funzionare anche dove nmap non c'è (per esempio in CI)."""

    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        d = Path(self._d.name)
        self.scope = str(d / "scope.toml")
        Path(self.scope).write_text(SCOPE)
        self.audit = str(d / "a.jsonl")
        self.cwd = os.getcwd()
        os.chdir(d)
        self.addCleanup(os.chdir, self.cwd)
        vecchio = os.environ["PATH"]
        os.environ["PATH"] = str(d)  # una cartella senza nmap
        self.addCleanup(os.environ.__setitem__, "PATH", vecchio)

    def test_dry_run_funziona_senza_nmap(self):
        rc, out, _ = run("scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit)
        self.assertEqual(rc, errors.OK)
        self.assertIn("anteprima", out)

    def test_esegui_senza_nmap_esce_con_5(self):
        rc, *_ = run(
            "scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit,
            "--esegui", "--conferma",
        )  # fmt: skip
        self.assertEqual(rc, errors.NMAP_ASSENTE)


class StdinTest(unittest.TestCase):
    """nmap non legge target da stdin senza -iL, ma il figlio non deve ereditare comunque lo stdin."""

    def test_stdin_non_arriva_al_tool(self):
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "bin").mkdir()
            finto = d / "bin" / "nmap"
            finto.write_text(
                '#!/bin/sh\nif [ "$1" = "--version" ]; then echo "Nmap version 0.0 ( https://nmap.org )"; exit 0; fi\n'
                "/bin/cat > stdin_visto\nexit 0\n"
            )
            finto.chmod(0o755)
            (d / "scope.toml").write_text(SCOPE)
            env = dict(os.environ, PYTHONPATH=str(Path(cli.__file__).parents[1]), PATH=str(d / "bin"))
            r = subprocess.run(
                [sys.executable, "-m", "nmapcli", "scansiona", "rapido", "127.0.0.1", "--scope", "scope.toml",
                 "--audit", "a.jsonl", "--esegui", "--conferma", "--out", "o"],
                input="evil.example.org\n", capture_output=True, text=True, env=env, cwd=d,
            )  # fmt: skip
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual((d / "stdin_visto").read_text(), "")


class ProgrammaOmonimoTest(unittest.TestCase):
    """Nel PATH può esserci un altro programma chiamato 'nmap' che non è Nmap."""

    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        d = Path(self._d.name)
        self.scope = str(d / "scope.toml")
        Path(self.scope).write_text(SCOPE)
        self.audit = str(d / "a.jsonl")
        self.cwd = os.getcwd()
        os.chdir(d)
        self.addCleanup(os.chdir, self.cwd)
        self.bin = d / "bin"
        self.bin.mkdir()
        (self.bin / "nmap").write_text("#!/bin/sh\necho 'un altro programma, versione 9.9'\nexit 0\n")
        (self.bin / "nmap").chmod(0o755)
        vecchio = os.environ["PATH"]
        os.environ["PATH"] = str(self.bin)
        self.addCleanup(os.environ.__setitem__, "PATH", vecchio)

    def test_esegui_viene_rifiutato(self):
        rc, _, err = run(
            "scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit,
            "--esegui", "--conferma",
        )  # fmt: skip
        self.assertEqual(rc, errors.NMAP_ASSENTE)
        self.assertIn("non sembra nmap", err)
        self.assertFalse(Path(self.audit).exists())

    def test_dry_run_non_controlla_l_identita(self):
        # il dry-run non lancia nulla: non ha bisogno di sapere se il binario è quello giusto.
        rc, out, _ = run("scansiona", "rapido", "127.0.0.1", "--scope", self.scope, "--audit", self.audit)
        self.assertEqual(rc, errors.OK)
        self.assertIn("Dry-run", out)

    def test_doctor_rifiuta_il_binario_sbagliato(self):
        rc, _, err = run("doctor")
        self.assertEqual(rc, errors.NMAP_ASSENTE)
        self.assertIn("non sembra nmap", err)


class BannerTest(unittest.TestCase):
    def test_a_mani_vuote_mostra_logo_e_suggerimento(self):
        rc, out, err = run()
        self.assertEqual(rc, errors.OK)
        self.assertIn("scope-first", err)  # la tagline del banner
        self.assertIn("guida", err)  # il suggerimento


class GuidaTest(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.addCleanup(self._d.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self._d.name)
        self.addCleanup(os.chdir, self.cwd)

    def guida(self, inputs):
        with mock.patch("sys.stdin.isatty", return_value=True), mock.patch("builtins.input", side_effect=inputs):
            return run("guida")

    def test_non_interattivo_rifiutato(self):
        with mock.patch("sys.stdin.isatty", return_value=False):
            rc, _, err = run("guida")
        self.assertEqual(rc, errors.USO)
        self.assertIn("interattivo", err)

    def test_dry_run_non_lancia_niente(self):
        Path("scope.toml").write_text(SCOPE)
        rc, out, _ = self.guida(["scope.toml", "rapido", "127.0.0.1", "no"])
        self.assertEqual(rc, errors.OK, out)
        self.assertIn("Dry-run", out)
        self.assertFalse(Path("out").exists())

    def test_target_fuori_scope(self):
        Path("scope.toml").write_text(SCOPE)
        rc, _, _ = self.guida(["scope.toml", "rapido", "8.8.8.8", "no"])
        self.assertEqual(rc, errors.FUORI_SCOPE)

    def test_profilo_scelto_per_numero(self):
        Path("scope.toml").write_text(SCOPE)
        rc, out, _ = self.guida(["scope.toml", "1", "127.0.0.1", "no"])
        self.assertEqual(rc, errors.OK, out)

    def test_profilo_sbagliato(self):
        Path("scope.toml").write_text(SCOPE)
        rc, _, err = self.guida(["scope.toml", "profilo-che-non-esiste"])
        self.assertEqual(rc, errors.USO)
        self.assertIn("profilo", err)

    def test_scope_mancante_offre_di_crearlo(self):
        rc, _, _ = self.guida(["nuovo.toml", "s"])
        self.assertEqual(rc, errors.OK)
        self.assertTrue(Path("nuovo.toml").exists())
