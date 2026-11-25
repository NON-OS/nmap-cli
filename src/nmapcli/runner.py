"""Costruzione ed esecuzione del comando nmap. Mai una shell: solo liste di argomenti."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from nmapcli import i18n
from nmapcli.errors import NmapAssente
from nmapcli.profiles import Profilo

VERSIONE_MINIMA = (7, 90)
_RE_VERSIONE = re.compile(r"Nmap version (\d+)\.(\d+)")


def trova_nmap() -> str:
    percorso = shutil.which("nmap")
    if not percorso:
        raise NmapAssente(i18n.t("run_non_trovato"))
    return percorso


def _testo_versione(binario: str) -> str:
    """Output completo di --version, stdout e stderr insieme."""
    try:
        r = subprocess.run(
            [binario, "--version"], capture_output=True, text=True, timeout=10, check=False,
            stdin=subprocess.DEVNULL,
        )  # fmt: skip
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout + "\n" + r.stderr


def versione(binario: str) -> tuple[int, int] | None:
    m = _RE_VERSIONE.search(_testo_versione(binario))
    return (int(m.group(1)), int(m.group(2))) if m else None


def verifica_identita(binario: str) -> None:
    """Controlla che il binario trovato nel PATH sia davvero nmap, non un omonimo."""
    if "nmap version" not in _testo_versione(binario).lower():
        raise NmapAssente(i18n.t("run_non_sembra", binario=binario))


@dataclass(frozen=True)
class Comando:
    argv: tuple[str, ...]
    prefisso_output: Path


def costruisci(
    binario: str,
    profilo: Profilo,
    target: list[str],
    extra: list[str],
    cartella_output: Path,
) -> Comando:
    prefisso = cartella_output / "scan"
    argv = (
        binario,
        *profilo.args,
        *extra,
        "-oA",
        str(prefisso),
        "--",
        *target,
    )
    return Comando(argv, prefisso)


def esegui(cmd: Comando) -> int:
    cmd.prefisso_output.parent.mkdir(parents=True, exist_ok=True)
    # stdin chiuso: nessun tool deve poter ricevere target da una pipe, fuori dal controllo dello scope
    return subprocess.run(cmd.argv, check=False, stdin=subprocess.DEVNULL).returncode
