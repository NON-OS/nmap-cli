"""Lettura dell'XML di nmap, report e confronto tra due scansioni.

Solo libreria standard. L'XML che produce nmap non definisce entità proprie,
e expat (da Python 3.7.1) limita comunque l'espansione: nessun parser esterno.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path

from nmapcli import i18n
from nmapcli.errors import NmapCliError


class XmlIllegibile(NmapCliError):
    pass


# -- dati che arrivano dal bersaglio -----------------------------------------
#
# L'hostname (reverse DNS), il nome del servizio, la versione e il sistema
# operativo stimato non li scrive l'operatore: li restituisce la macchina
# scansionata, che può essere ostile. Un servizio può rispondere con un
# banner che contiene newline per "aprire" una riga nuova nel report di
# testo, o caratteri come '#' e '|' per iniettare un'intestazione o rompere
# una tabella Markdown — e un report Markdown, prima o poi, qualcuno lo
# incollerà in uno strumento che include un modello linguistico ("riassumimi
# questa scansione"), dove quelle righe false diventano testo che il modello
# legge insieme al resto.
#
# La difesa qui non cerca di riconoscere un tentativo di iniezione: cercare
# frasi sospette è un filtro che si aggira riformulando. Si toglie invece il
# potere strutturale al dato — niente più a capo, niente più caratteri che
# significano qualcosa per Markdown — così qualunque cosa il bersaglio provi
# a scrivere resta testo su una riga sola, dentro la cella o le parentesi che
# le competono, e non può diventare una riga, un titolo o una cella in più.
_CONTROLLO = re.compile(r"[\x00-\x1f\x7f]+")


def _testo_bersaglio(grezzo: str, *, max_lunghezza: int = 200) -> str:
    """Neutralizza un valore letto dal bersaglio (hostname, servizio, versione, OS).

    Non cambia il significato per un umano che legge il report: toglie solo la
    possibilità di spezzare la riga o la struttura del documento. I dati nel
    modello (Host, Porta) restano quelli grezzi di nmap; solo i formati pensati
    per essere letti direttamente — testo e Markdown — passano da qui. Il JSON
    non ne ha bisogno: ``json.dumps`` già esegue l'escape dei caratteri di
    controllo dentro una stringa, quindi resta strutturalmente al sicuro.
    """
    pulito = " ".join(_CONTROLLO.sub(" ", grezzo).split())
    if len(pulito) > max_lunghezza:
        pulito = pulito[: max_lunghezza - 1].rstrip() + "…"
    return pulito


def _cella_markdown(grezzo: str) -> str:
    """Come _testo_bersaglio, ma protegge anche una cella di tabella Markdown."""
    return _testo_bersaglio(grezzo).replace("|", "\\|")


@dataclass(frozen=True)
class Porta:
    numero: int
    proto: str
    stato: str
    servizio: str = ""
    versione: str = ""

    @property
    def chiave(self) -> str:
        return f"{self.numero}/{self.proto}"


@dataclass
class Host:
    indirizzo: str
    nome: str = ""
    attivo: bool = True
    porte: list[Porta] = field(default_factory=list)
    sistema: str = ""

    def aperte(self) -> list[Porta]:
        return [p for p in self.porte if p.stato == "open"]


@dataclass
class Scansione:
    comando: str
    inizio: str
    host: list[Host] = field(default_factory=list)


def leggi(percorso: str | Path) -> Scansione:
    try:
        radice = ET.parse(percorso).getroot()
    except FileNotFoundError:
        raise XmlIllegibile(i18n.t("rp_non_trovato", p=percorso)) from None
    except ET.ParseError as e:
        raise XmlIllegibile(i18n.t("rp_xml_invalido", p=percorso, e=e)) from None
    if radice.tag != "nmaprun":
        raise XmlIllegibile(i18n.t("rp_non_nmap", p=percorso))

    scan = Scansione(radice.get("args", ""), radice.get("startstr", ""))
    for h in radice.findall("host"):
        stato = h.find("status")
        addr = next((a for a in h.findall("address") if a.get("addrtype") in ("ipv4", "ipv6")), None)
        if addr is None:
            continue
        nome = h.find("hostnames/hostname")
        host = Host(
            indirizzo=addr.get("addr", ""),
            nome=nome.get("name", "") if nome is not None else "",
            attivo=stato is None or stato.get("state") == "up",
        )
        for p in h.findall("ports/port"):
            st = p.find("state")
            sv = p.find("service")
            versione = ""
            if sv is not None:
                versione = " ".join(x for x in (sv.get("product"), sv.get("version")) if x)
            host.porte.append(
                Porta(
                    int(p.get("portid", "0")),
                    p.get("protocol", "tcp"),
                    st.get("state", "?") if st is not None else "?",
                    sv.get("name", "") if sv is not None else "",
                    versione,
                )
            )
        os_ = h.find("os/osmatch")
        if os_ is not None:
            host.sistema = f"{os_.get('name', '')} ({os_.get('accuracy', '?')}%)"
        scan.host.append(host)
    return scan


# -- report -----------------------------------------------------------------


def a_json(scan: Scansione) -> str:
    return json.dumps(asdict(scan), indent=2, ensure_ascii=False)


def a_markdown(scan: Scansione) -> str:
    attivi = [h for h in scan.host if h.attivo]
    righe = [
        i18n.t("rp_titolo"),
        "",
        i18n.t("rp_comando", cmd=scan.comando),
        i18n.t("rp_inizio", inizio=scan.inizio or i18n.t("rp_nd")),
        i18n.t("rp_attivi", attivi=len(attivi), totale=len(scan.host)),
        i18n.t("rp_porte_tot", n=sum(len(h.aperte()) for h in attivi)),
        "",
    ]
    for h in attivi:
        nome = _testo_bersaglio(h.nome) if h.nome else ""
        titolo = h.indirizzo + (f" ({nome})" if nome else "")
        righe += [f"## {titolo}", ""]
        if h.sistema:
            righe += [i18n.t("rp_os", os=_testo_bersaglio(h.sistema)), ""]
        aperte = h.aperte()
        if not aperte:
            righe += [i18n.t("rp_nessuna_md"), ""]
            continue
        righe += [i18n.t("rp_tabella"), "|---|---|---|"]
        righe += [
            f"| {p.chiave} | {_cella_markdown(p.servizio) or '-'} | {_cella_markdown(p.versione) or '-'} |"
            for p in aperte
        ]
        righe.append("")
    return "\n".join(righe)


def a_testo(scan: Scansione) -> str:
    out: list[str] = []
    for h in scan.host:
        if not h.attivo:
            continue
        nome = _testo_bersaglio(h.nome) if h.nome else ""
        out.append(f"{h.indirizzo}" + (f"  {nome}" if nome else ""))
        for p in h.aperte():
            servizio, versione = _testo_bersaglio(p.servizio), _testo_bersaglio(p.versione)
            out.append(f"  {p.chiave:<10} {servizio:<14} {versione}".rstrip())
        if not h.aperte():
            out.append(i18n.t("rp_nessuna"))
    return "\n".join(out)


# -- confronto --------------------------------------------------------------


@dataclass
class Differenze:
    host_nuovi: list[str] = field(default_factory=list)
    host_spariti: list[str] = field(default_factory=list)
    porte_aperte: list[tuple[str, str]] = field(default_factory=list)
    porte_chiuse: list[tuple[str, str]] = field(default_factory=list)
    versioni_cambiate: list[tuple[str, str, str, str]] = field(default_factory=list)

    def vuoto(self) -> bool:
        return not any(
            (self.host_nuovi, self.host_spariti, self.porte_aperte, self.porte_chiuse, self.versioni_cambiate)
        )


def confronta(vecchia: Scansione, nuova: Scansione) -> Differenze:
    def mappa(s: Scansione) -> dict[str, dict[str, Porta]]:
        return {h.indirizzo: {p.chiave: p for p in h.aperte()} for h in s.host if h.attivo}

    a, b = mappa(vecchia), mappa(nuova)
    d = Differenze(host_nuovi=sorted(b.keys() - a.keys()), host_spariti=sorted(a.keys() - b.keys()))
    for ip in sorted(a.keys() & b.keys()):
        for k in sorted(b[ip].keys() - a[ip].keys()):
            d.porte_aperte.append((ip, k))
        for k in sorted(a[ip].keys() - b[ip].keys()):
            d.porte_chiuse.append((ip, k))
        for k in sorted(a[ip].keys() & b[ip].keys()):
            va, vb = a[ip][k].versione, b[ip][k].versione
            if va != vb:
                d.versioni_cambiate.append((ip, k, va or "-", vb or "-"))
    return d


def differenze_a_testo(d: Differenze) -> str:
    if d.vuoto():
        return i18n.t("df_nessuna")
    out: list[str] = []
    out += [i18n.t("df_host_nuovo", x=x) for x in d.host_nuovi]
    out += [i18n.t("df_host_sparito", x=x) for x in d.host_spariti]
    out += [i18n.t("df_porta_aperta", ip=ip, p=p) for ip, p in d.porte_aperte]
    out += [i18n.t("df_porta_chiusa", ip=ip, p=p) for ip, p in d.porte_chiuse]
    out += [
        i18n.t("df_versione", ip=ip, p=p, da=_testo_bersaglio(a), a=_testo_bersaglio(b))
        for ip, p, a, b in d.versioni_cambiate
    ]
    return "\n".join(out)
