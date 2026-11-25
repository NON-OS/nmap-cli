"""Interfaccia a riga di comando."""

from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import sys
from datetime import datetime
from pathlib import Path

from nmapcli import __version__, audit, errors, firma, i18n, profiles, rapporto, runner
from nmapcli import scope as scope_mod

AVVISO = i18n.MSG["avviso"]["it"]

_SI = i18n.si_accettati()

_LOGO = r"""
 ███╗   ██╗  ██████╗  ███╗   ██╗  ██████╗  ███████╗
 ████╗  ██║ ██╔═══██╗ ████╗  ██║ ██╔═══██╗ ██╔════╝
 ██╔██╗ ██║ ██║   ██║ ██╔██╗ ██║ ██║   ██║ ███████╗
 ██║╚██╗██║ ██║   ██║ ██║╚██╗██║ ██║   ██║ ╚════██║
 ██║ ╚████║ ╚██████╔╝ ██║ ╚████║ ╚██████╔╝ ███████║
 ╚═╝  ╚═══╝  ╚═════╝  ╚═╝  ╚═══╝  ╚═════╝  ╚══════╝"""


def _banner() -> None:
    """Logo NONOS su stderr, così non inquina mai stdout (rapporto --json, confronta, pipe)."""
    try:
        print(_LOGO, file=sys.stderr)
        print(i18n.t("banner_sub", ver=__version__) + "\n", file=sys.stderr)
    except Exception:
        pass


MODELLO_SCOPE = """\
# Scope dell'ingaggio. Compilalo a mano, con il cliente, prima di scansionare.
# Se un campo non lo sai riempire, non sei pronto a lanciare nulla.

[engagement]
nome = "NOME-INGAGGIO"
autorizzato_da = "Nome Cognome, ruolo, azienda"
riferimento = "ID contratto o lettera di autorizzazione"
valido_dal = 2026-01-01
valido_fino = 2026-01-31

[scope]
# IP singoli, reti CIDR (esatte, senza bit d'host), hostname, "*.dominio.tld"
include = [
    "192.0.2.0/24",
    "lab.example.org",
]
# Ha sempre la precedenza su include.
esclude = [
    "192.0.2.1",
]
"""

# Stesso file, commenti ed esempi nella lingua scelta. Le chiavi TOML non cambiano mai.
MODELLI_SCOPE = {
    "it": MODELLO_SCOPE,
    "en": """\
# Engagement scope. Fill it in by hand, with the client, before scanning.
# If there is a field you cannot fill in, you are not ready to run anything.

[engagement]
nome = "ENGAGEMENT-NAME"
autorizzato_da = "Full name, role, company"
riferimento = "Contract ID or authorization letter"
valido_dal = 2026-01-01
valido_fino = 2026-01-31

[scope]
# Single IPs, CIDR networks (exact, no host bits), hostnames, "*.domain.tld"
include = [
    "192.0.2.0/24",
    "lab.example.org",
]
# Always takes precedence over include.
esclude = [
    "192.0.2.1",
]
""",
    "zh": """\
# 项目作用域。扫描之前，请和客户一起手工填写。
# 如果有哪个字段你填不出来，说明你还没准备好运行任何东西。

[engagement]
nome = "项目名称"
autorizzato_da = "姓名、职务、公司"
riferimento = "合同编号或授权书编号"
valido_dal = 2026-01-01
valido_fino = 2026-01-31

[scope]
# 单个 IP、CIDR 网段（精确，不带主机位）、主机名、"*.domain.tld"
include = [
    "192.0.2.0/24",
    "lab.example.org",
]
# 始终优先于 include。
esclude = [
    "192.0.2.1",
]
""",
}


def _modello_scope() -> str:
    return MODELLI_SCOPE.get(i18n.lingua(), MODELLO_SCOPE)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="nmap-cli",
        description=i18n.t("descrizione"),
        epilog=i18n.t("avviso"),
    )
    p.add_argument("--version", action="version", version=f"nmap-cli {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scansiona", help=i18n.t("help_scansiona"))
    s.add_argument("profilo", choices=sorted(profiles.PROFILI))
    s.add_argument("target", nargs="+")
    s.add_argument("--scope", required=True, metavar="FILE")
    _argomenti_firma(s)
    s.add_argument("--esegui", action="store_true", help=i18n.t("help_esegui"))
    s.add_argument("--conferma", action="store_true", help=i18n.t("help_conferma"))
    s.add_argument("--out", metavar="DIR", help=i18n.t("help_out"))
    s.add_argument("--audit", default="nmap-cli.audit.jsonl", metavar="FILE")

    c = sub.add_parser("verifica", help=i18n.t("help_verifica"))
    c.add_argument("target", nargs="+")
    c.add_argument("--scope", required=True, metavar="FILE")
    _argomenti_firma(c)

    sf = sub.add_parser("scope-firma", help=i18n.t("help_scope_firma"))
    sf.add_argument("scope", metavar="FILE")
    sf.add_argument("--chiave", required=True, metavar=i18n.t("mv_chiave"))

    sv = sub.add_parser("scope-verifica", help=i18n.t("help_scope_verifica"))
    sv.add_argument("scope", metavar="FILE")
    sv.add_argument("--firmatari", required=True, metavar="FILE")
    sv.add_argument("--firma", metavar="FILE", help=i18n.t("help_firma_default"))

    sub.add_parser("profili", help=i18n.t("help_profili"))

    a = sub.add_parser("audit", help=i18n.t("help_audit"))
    a.add_argument("file", nargs="?", default="nmap-cli.audit.jsonl")

    i = sub.add_parser("init", help=i18n.t("help_init"))
    i.add_argument("percorso", nargs="?", default="scope.toml")

    sub.add_parser("doctor", help=i18n.t("help_doctor"))

    sub.add_parser("guida", help=i18n.t("help_guida"))

    r = sub.add_parser("rapporto", help=i18n.t("help_rapporto"))
    r.add_argument("xml", metavar="scan.xml")
    r.add_argument("--formato", choices=("testo", "markdown", "json"), default="testo")

    f = sub.add_parser("confronta", help=i18n.t("help_confronta"))
    f.add_argument("vecchia", metavar=i18n.t("mv_vecchia_xml"))
    f.add_argument("nuova", metavar=i18n.t("mv_nuova_xml"))
    f.add_argument("--exit-code", action="store_true", help=i18n.t("help_exit_code"))
    return p


def _argomenti_firma(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--firmatari", metavar="FILE",
        help=i18n.t("help_firmatari"),
    )  # fmt: skip
    p.add_argument("--firma", metavar="FILE", help=i18n.t("help_firma_staccata"))


def _carica_scope(a: argparse.Namespace) -> tuple[scope_mod.Scope, str, firma.Firmatario | None]:
    """Legge lo scope una volta sola, verifica la firma se richiesta sugli stessi byte, ritorna anche l'hash."""
    try:
        grezzo = Path(a.scope).read_bytes()
    except FileNotFoundError:
        raise errors.ScopeInvalido(i18n.t("sc_non_trovato", p=a.scope)) from None
    chi = None
    if getattr(a, "firmatari", None):
        chi = firma.verifica(grezzo, getattr(a, "firma", None) or firma.percorso_firma(a.scope), a.firmatari)
    sc = scope_mod.carica(a.scope, grezzo)
    sc.verifica_validita()
    return sc, hashlib.sha256(grezzo).hexdigest(), chi


def _scrivi(msg: str = "") -> None:
    print(msg)


def _err(msg: str) -> None:
    print(f"nmap-cli: {msg}", file=sys.stderr)


# -- comandi ---------------------------------------------------------------


def _scansiona(a: argparse.Namespace, extra: list[str]) -> int:
    profilo = profiles.PROFILI[a.profilo]
    profiles.filtra_extra(extra)

    sc, scope_hash, chi = _carica_scope(a)
    esiti = sc.richiedi(a.target)

    nota_binario = ""
    try:
        binario = runner.trova_nmap()
        if a.esegui:
            runner.verifica_identita(binario)
    except errors.NmapAssente:
        if a.esegui:
            raise
        binario = "nmap"
        nota_binario = i18n.t("nota_binario")
    cartella = Path(a.out) if a.out else Path("out") / f"{datetime.now():%Y%m%d-%H%M%S}-{profilo.nome}"
    cmd = runner.costruisci(binario, profilo, [e.target for e in esiti], extra, cartella)

    base = {
        "ingaggio": sc.nome,
        "riferimento": sc.riferimento,
        "scope_sha256": scope_hash,
        "scope_firmato_da": chi.identita if chi else None,
        "scope_firma_fp": chi.impronta if chi else None,
        "profilo": profilo.nome,
        "target": [e.target for e in esiti],
        "argv": list(cmd.argv),
        "utente": os.environ.get("USER", "?"),
    }

    _scrivi(i18n.t("out_ingaggio", nome=sc.nome, rif=sc.riferimento))
    if chi:
        _scrivi(i18n.t("out_firma", id=chi.identita, fp=chi.impronta))
    _scrivi(i18n.t("out_profilo", nome=profilo.nome, desc=profilo.descrizione, rumore=i18n.rumore(profilo.rumore)))
    for e in esiti:
        _scrivi(i18n.t("out_ok", target=e.target, motivo=e.motivo))
    _scrivi(i18n.t("out_comando", cmd=shlex.join(cmd.argv)))

    if nota_binario:
        _scrivi(i18n.t("out_nota", nota=nota_binario))
    if profilo.richiede_root and os.geteuid() != 0:
        _scrivi(i18n.t("out_nota_root", nome=profilo.nome))

    if not a.esegui:
        audit.registra(a.audit, "dry_run", **base)
        _scrivi(i18n.t("out_dry_run"))
        return errors.OK

    if profilo.richiede_root and os.geteuid() != 0:
        _err(i18n.t("err_sudo", nome=profilo.nome))
        return errors.RIFIUTATO
    if not _confermato(a.conferma, sc):
        audit.registra(a.audit, "rifiutato", **base)
        _err(i18n.t("err_conferma"))
        return errors.RIFIUTATO

    audit.registra(a.audit, "avviata", **base)
    sys.stdout.flush()  # senza, l'output di nmap finisce prima della nostra intestazione
    rc = runner.esegui(cmd)
    audit.registra(a.audit, "conclusa", ingaggio=sc.nome, argv=list(cmd.argv), codice_nmap=rc)
    if rc != 0:
        _err(i18n.t("err_codice", rc=rc))
        return errors.FALLITO
    _scrivi(i18n.t("out_risultati", cartella=cmd.prefisso_output.parent))
    return errors.OK


def _confermato(gia: bool, sc: scope_mod.Scope) -> bool:
    if gia:
        return True
    if not sys.stdin.isatty():
        return False
    _scrivi(i18n.t("conf_intro", auth=sc.autorizzato_da))
    risposta = input(i18n.t("conf_prompt", rif=sc.riferimento))
    return risposta.strip() == sc.riferimento


def _verifica(a: argparse.Namespace) -> int:
    sc, _, _ = _carica_scope(a)
    fuori = 0
    for t in a.target:
        v = sc.controlla(t)
        _scrivi(f"{i18n.t('ver_ok') if v.ammesso else i18n.t('ver_no')} {v.target}  {v.motivo}")
        fuori += not v.ammesso
    return errors.FUORI_SCOPE if fuori else errors.OK


def _scope_firma(a: argparse.Namespace) -> int:
    sig = firma.firma(a.scope, a.chiave)
    _scrivi(i18n.t("firma_fatto", sig=sig))
    _scrivi(i18n.t("firma_consegna"))
    return errors.OK


def _scope_verifica(a: argparse.Namespace) -> int:
    chi = firma.verifica(Path(a.scope).read_bytes(), a.firma or firma.percorso_firma(a.scope), a.firmatari)
    _scrivi(i18n.t("scopever_ok", id=chi.identita, fp=chi.impronta))
    return errors.OK


def _profili() -> int:
    for p in profiles.PROFILI.values():
        root = " (root)" if p.richiede_root else ""
        _scrivi(f"{p.nome:<14} {i18n.t('lbl_rumore')} {i18n.rumore(p.rumore):<6}{root}")
        _scrivi(f"  {p.descrizione}")
        _scrivi(f"  {i18n.t('lbl_quando')}: {p.quando}")
        _scrivi(f"  Flag  : {' '.join(p.args)}")
        _scrivi()
    return errors.OK


def _audit(a: argparse.Namespace) -> int:
    r = audit.verifica(a.file)
    if r.valido:
        _scrivi(i18n.t("audit_ok", righe=r.righe))
        return errors.OK
    _err(i18n.t("audit_ko", errore=r.errore))
    return errors.FALLITO


def _init(a: argparse.Namespace) -> int:
    p = Path(a.percorso)
    if p.exists():
        _err(i18n.t("init_esiste", p=p))
        return errors.USO
    p.write_text(_modello_scope())
    _scrivi(i18n.t("init_creato", p=p))
    return errors.OK


def _doctor() -> int:
    try:
        b = runner.trova_nmap()
    except errors.NmapAssente as e:
        _err(str(e))
        return e.exit_code
    v = runner.versione(b)
    _scrivi(f"nmap      : {b}")
    _scrivi(i18n.t("doc_versione", v=".".join(map(str, v)) if v else i18n.t("non_riconosciuta")))
    try:
        runner.verifica_identita(b)
    except errors.NmapAssente as e:
        _err(str(e))
        return e.exit_code
    if v and v < runner.VERSIONE_MINIMA:
        _err(i18n.t("doc_minima", v=".".join(map(str, runner.VERSIONE_MINIMA))))
        return errors.NMAP_ASSENTE
    _scrivi(f"{'root':<10}: {i18n.t('root_si') if os.geteuid() == 0 else i18n.t('root_no')}")
    _scrivi(f"python    : {sys.version.split()[0]}")
    return errors.OK


def _rapporto(a: argparse.Namespace) -> int:
    scan = rapporto.leggi(a.xml)
    rese = {"testo": rapporto.a_testo, "markdown": rapporto.a_markdown, "json": rapporto.a_json}
    _scrivi(rese[a.formato](scan))
    return errors.OK


def _confronta(a: argparse.Namespace) -> int:
    d = rapporto.confronta(rapporto.leggi(a.vecchia), rapporto.leggi(a.nuova))
    _scrivi(rapporto.differenze_a_testo(d))
    return 1 if (a.exit_code and not d.vuoto()) else errors.OK


def _scegli_profilo(scelta: str) -> str | None:
    """Accetta il nome di un profilo o il suo numero nella lista."""
    nomi = list(profiles.PROFILI)
    if scelta in profiles.PROFILI:
        return scelta
    if scelta.isdigit() and 1 <= int(scelta) <= len(nomi):
        return nomi[int(scelta) - 1]
    return None


def _guida(_a: argparse.Namespace) -> int:
    """Modalità interattiva: raccoglie le scelte e poi delega a _scansiona, che fa i controlli veri."""
    _banner()
    if not sys.stdin.isatty():
        _err(i18n.t("guida_tty"))
        return errors.USO
    _scrivi(i18n.t("guida_intro"))

    percorso = input(i18n.t("prompt_scope")).strip() or "scope.toml"
    if not Path(percorso).exists():
        if input(i18n.t("prompt_crea_scope", percorso=percorso)).strip().lower() in _SI:
            Path(percorso).write_text(_modello_scope())
            _scrivi(i18n.t("scope_creato", percorso=percorso))
        return errors.OK
    try:
        sc = scope_mod.carica(percorso)
        sc.verifica_validita()
    except errors.NmapCliError as e:
        _err(str(e))
        return e.exit_code
    _scrivi(i18n.t("guida_ingaggio", nome=sc.nome, rif=sc.riferimento, auth=sc.autorizzato_da))

    _scrivi(i18n.t("profili_disponibili"))
    for n, p in enumerate(profiles.PROFILI.values(), 1):
        root = " [root]" if p.richiede_root else ""
        _scrivi(f"  {n:>2}) {p.nome:<14} {i18n.t('lbl_rumore')} {i18n.rumore(p.rumore)}{root} — {p.descrizione}")
    profilo = _scegli_profilo(input(i18n.t("prompt_profilo")).strip())
    if profilo is None:
        _err(i18n.t("profilo_no"))
        return errors.USO

    target = input(i18n.t("prompt_target", profilo=profilo)).split()
    if not target:
        _err(i18n.t("target_no"))
        return errors.USO

    esegui = input(i18n.t("prompt_esegui")).strip().lower() in _SI
    ns = argparse.Namespace(
        profilo=profilo,
        target=target,
        scope=percorso,
        esegui=esegui,
        conferma=False,
        out=None,
        audit="nmap-cli.audit.jsonl",
        firmatari=None,
        firma=None,
    )
    _scrivi("")
    return _scansiona(ns, [])


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    # Tutto ciò che segue '--' è passato a nmap, dopo il filtro dei flag vietati.
    extra: list[str] = []
    if "--" in args:
        i = args.index("--")
        args, extra = args[:i], args[i + 1 :]

    lingua_override = None
    for i, arg in enumerate(args):
        if arg == "--lang" and i + 1 < len(args):
            lingua_override = args[i + 1]
            del args[i : i + 2]
            break
        if arg.startswith("--lang="):
            lingua_override = arg.split("=", 1)[1]
            del args[i]
            break
    i18n.imposta_lingua(lingua_override)
    profiles.applica_lingua(i18n.lingua())
    # usage, options ed errori di argparse passano da gettext: li traduciamo noi.
    argparse._ = i18n.argparse_gettext  # type: ignore[attr-defined]

    if not args:
        _banner()
        print(i18n.t("hint_guida"), file=sys.stderr)
        print(i18n.t("hint_help"), file=sys.stderr)
        return errors.OK

    parser = _parser()
    a = parser.parse_args(args)
    if extra and a.cmd != "scansiona":
        parser.error(i18n.t("err_extra"))

    try:
        if a.cmd == "scansiona":
            return _scansiona(a, extra)
        if a.cmd == "verifica":
            return _verifica(a)
        if a.cmd == "scope-firma":
            return _scope_firma(a)
        if a.cmd == "scope-verifica":
            return _scope_verifica(a)
        if a.cmd == "profili":
            return _profili()
        if a.cmd == "audit":
            return _audit(a)
        if a.cmd == "init":
            return _init(a)
        if a.cmd == "doctor":
            return _doctor()
        if a.cmd == "guida":
            return _guida(a)
        if a.cmd == "rapporto":
            return _rapporto(a)
        if a.cmd == "confronta":
            return _confronta(a)
    except errors.NmapCliError as e:
        _err(str(e))
        return e.exit_code
    except (KeyboardInterrupt, EOFError):
        _err(i18n.t("err_interrotto"))
        return 130
    return errors.USO


if __name__ == "__main__":
    raise SystemExit(main())
