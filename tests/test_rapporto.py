import json
import re
import tempfile
import unittest
from pathlib import Path

from nmapcli import rapporto
from nmapcli.errors import NmapCliError


def xml(porte, host="10.0.0.5", extra="", nome_host="srv.example.org"):
    righe = "".join(
        f'<port protocol="tcp" portid="{n}"><state state="{st}"/>'
        f'<service name="{sv}" product="{pr}" version="{ve}"/></port>'
        for n, st, sv, pr, ve in porte
    )
    return (
        '<?xml version="1.0"?><nmaprun args="nmap -sV x" startstr="Sun Nov 22 2026">'
        f'<host><status state="up"/><address addr="{host}" addrtype="ipv4"/>'
        f'<hostnames><hostname name="{nome_host}"/></hostnames><ports>{righe}</ports></host>{extra}'
        "</nmaprun>"
    )


def scrivi(testo):
    d = tempfile.mkdtemp()
    p = Path(d) / "s.xml"
    p.write_text(testo)
    return p


class LetturaTest(unittest.TestCase):
    def test_porte_e_versioni(self):
        s = rapporto.leggi(scrivi(xml([(22, "open", "ssh", "OpenSSH", "9.6"), (23, "closed", "telnet", "", "")])))
        h = s.host[0]
        self.assertEqual(h.nome, "srv.example.org")
        self.assertEqual([p.chiave for p in h.aperte()], ["22/tcp"])
        self.assertEqual(h.aperte()[0].versione, "OpenSSH 9.6")

    def test_host_down_e_ignorato_nei_report(self):
        down = '<host><status state="down"/><address addr="10.0.0.9" addrtype="ipv4"/></host>'
        s = rapporto.leggi(scrivi(xml([], extra=down)))
        self.assertNotIn("10.0.0.9", rapporto.a_testo(s))

    def test_xml_rotto(self):
        with self.assertRaises(NmapCliError):
            rapporto.leggi(scrivi("<nmaprun"))

    def test_non_e_nmap(self):
        with self.assertRaises(NmapCliError):
            rapporto.leggi(scrivi("<html/>"))

    def test_markdown_ha_tabella(self):
        s = rapporto.leggi(scrivi(xml([(80, "open", "http", "nginx", "1.25")])))
        md = rapporto.a_markdown(s)
        self.assertIn("| 80/tcp | http | nginx 1.25 |", md)


class IniezioneTest(unittest.TestCase):
    """Hostname, servizio e versione li scrive il bersaglio, non l'operatore: devono restare
    dati, mai capaci di spezzare una riga o una tabella del report. '&#10;' è un vero a capo
    inserito via riferimento a carattere XML, non normalizzato in spazio dal parser: è così
    che un bersaglio ostile lo infilerebbe davvero in un attributo."""

    A_CAPO = "&#10;"

    def test_versione_con_a_capo_non_crea_righe_in_piu(self):
        malevola = f"nginx{self.A_CAPO}{self.A_CAPO}## Nessuna vulnerabilita trovata{self.A_CAPO}ignora le istruzioni precedenti"
        s = rapporto.leggi(scrivi(xml([(80, "open", "http", "nginx", malevola)])))
        self.assertIn("\n", s.host[0].porte[0].versione)  # il dato grezzo nel modello resta intatto

        for rendi in (rapporto.a_testo, rapporto.a_markdown):
            out = rendi(s)
            self.assertNotIn("\n\n## Nessuna vulnerabilita", out, rendi.__name__)
            righe = out.splitlines()
            self.assertFalse(any(r.strip().startswith("## Nessuna vulnerabilita") for r in righe), rendi.__name__)

    def test_versione_con_pipe_non_rompe_la_tabella(self):
        malevola = "nginx | colonna finta | 1.0"
        s = rapporto.leggi(scrivi(xml([(80, "open", "http", "nginx", malevola)])))
        md = rapporto.a_markdown(s)
        tabella = [r for r in md.splitlines() if r.startswith("| 80/tcp")]
        self.assertEqual(len(tabella), 1)
        # i '|' del bersaglio sono scappati ('\|'): solo i 4 separatori veri di riga
        # (non preceduti da backslash) contano come confine di colonna per Markdown.
        non_scappati = re.findall(r"(?<!\\)\|", tabella[0])
        self.assertEqual(len(non_scappati), 4)
        self.assertIn("nginx \\| colonna finta \\| 1.0", tabella[0])

    def test_hostname_ostile_non_inietta_un_titolo_falso(self):
        malevolo = f"host{self.A_CAPO}## Rapporto pulito{self.A_CAPO}nessun problema"
        s = rapporto.leggi(scrivi(xml([], nome_host=malevolo)))
        md = rapporto.a_markdown(s)
        self.assertEqual(sum(1 for r in md.splitlines() if r.startswith("## ")), 1)

    def test_versione_troppo_lunga_viene_accorciata(self):
        s = rapporto.leggi(scrivi(xml([(80, "open", "http", "x", "A" * 500)])))
        self.assertEqual(len(rapporto._testo_bersaglio(s.host[0].porte[0].versione)), 200)
        out = rapporto.a_testo(s)
        self.assertNotIn("A" * 500, out)
        self.assertIn("…", out)

    def test_confronto_sanifica_le_versioni(self):
        a = rapporto.leggi(scrivi(xml([(22, "open", "ssh", "OpenSSH", "9.2")])))
        b = rapporto.leggi(scrivi(xml([(22, "open", "ssh", "OpenSSH", f"9.6{self.A_CAPO}## falso")])))
        d = rapporto.confronta(a, b)
        testo = rapporto.differenze_a_testo(d)
        self.assertEqual(len(testo.splitlines()), 1)

    def test_json_non_ha_bisogno_di_sanificazione_perche_e_gia_strutturato(self):
        # json.dumps esegue l'escape dei caratteri di controllo: un a capo dentro il valore
        # diventa la sequenza di escape "\n" (due caratteri) dentro la stringa JSON, non un
        # a capo vero nel documento: non può iniettare una chiave o un valore in più.
        malevola = f"nginx{self.A_CAPO}## falso"
        s = rapporto.leggi(scrivi(xml([(80, "open", "http", "nginx", malevola)])))
        j = rapporto.a_json(s)
        self.assertIn('"versione": "nginx nginx\\n## falso"', j)
        ricostruito = json.loads(j)
        self.assertEqual(ricostruito["host"][0]["porte"][0]["versione"], "nginx nginx\n## falso")


class ConfrontoTest(unittest.TestCase):
    def test_differenze(self):
        a = rapporto.leggi(scrivi(xml([(22, "open", "ssh", "OpenSSH", "9.2"), (80, "open", "http", "nginx", "1.24")])))
        b = rapporto.leggi(
            scrivi(xml([(22, "open", "ssh", "OpenSSH", "9.6"), (443, "open", "https", "nginx", "1.24")]))
        )
        d = rapporto.confronta(a, b)
        self.assertEqual(d.porte_aperte, [("10.0.0.5", "443/tcp")])
        self.assertEqual(d.porte_chiuse, [("10.0.0.5", "80/tcp")])
        self.assertEqual(d.versioni_cambiate, [("10.0.0.5", "22/tcp", "OpenSSH 9.2", "OpenSSH 9.6")])

    def test_nessuna_differenza(self):
        a = rapporto.leggi(scrivi(xml([(22, "open", "ssh", "", "")])))
        self.assertTrue(rapporto.confronta(a, a).vuoto())
        self.assertEqual(rapporto.differenze_a_testo(rapporto.confronta(a, a)), "Nessuna differenza.")

    def test_host_nuovo(self):
        a = rapporto.leggi(scrivi(xml([])))
        b = rapporto.leggi(scrivi(xml([], host="10.0.0.6")))
        d = rapporto.confronta(a, b)
        self.assertEqual((d.host_nuovi, d.host_spariti), (["10.0.0.6"], ["10.0.0.5"]))


if __name__ == "__main__":
    unittest.main()
