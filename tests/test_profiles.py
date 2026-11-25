import unittest

from nmapcli import profiles
from nmapcli.errors import ArgomentoVietato


class FiltroTest(unittest.TestCase):
    def vietato(self, *tok):
        with self.assertRaises(ArgomentoVietato):
            profiles.filtra_extra(list(tok))

    def test_target_da_file(self):
        self.vietato("-iL", "liste.txt")
        self.vietato("-iLliste.txt")

    def test_target_casuali(self):
        self.vietato("-iR", "100")

    def test_zombie_e_decoy(self):
        self.vietato("-sI", "1.2.3.4")
        self.vietato("-D", "RND:10")

    def test_output_attaccato(self):
        self.vietato("-oXfuori.xml")

    def test_script_con_uguale(self):
        self.vietato("--script=vuln")
        self.vietato("--SCRIPT", "x")

    def test_script_dalla_porta_di_servizio(self):
        # -sC e -A attivano gli script 'default': aggirerebbero il blocco di --script
        self.vietato("-sC")
        self.vietato("-A")

    def test_flag_innocui_passano(self):
        extra = ["-sV", "-Pn", "-sS", "-p", "22,80", "-d", "--reason", "-sn"]
        self.assertEqual(profiles.filtra_extra(extra), extra)

    def test_valori_non_sono_flag(self):
        profiles.filtra_extra(["-p", "80", "--max-rate", "100"])

    def test_ogni_profilo_ha_testi(self):
        for p in profiles.PROFILI.values():
            self.assertTrue(p.descrizione and p.quando and p.args, p.nome)
            self.assertIn(p.rumore, {"basso", "medio", "alto"})

    def test_nessun_profilo_porta_flag_vietati(self):
        for p in profiles.PROFILI.values():
            for tok in p.args:
                if tok == "--script":
                    continue  # lo usa solo il profilo, con una categoria sicura
                profiles.filtra_extra([tok])


if __name__ == "__main__":
    unittest.main()
