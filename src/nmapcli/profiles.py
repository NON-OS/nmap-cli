"""Profili di scansione e filtro sugli argomenti passati a mano.

I profili sono volutamente pochi e prudenti. Niente script intrusivi, niente
zombie, niente decoy: chi ha bisogno di quelle cose ha anche bisogno di
parlare col cliente, e non è un lavoro per un flag.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from nmapcli import i18n
from nmapcli.errors import ArgomentoVietato


@dataclass(frozen=True)
class Profilo:
    nome: str
    descrizione: str
    args: tuple[str, ...]
    richiede_root: bool
    rumore: str  # "basso" | "medio" | "alto"
    quando: str


PROFILI: dict[str, Profilo] = {
    p.nome: p
    for p in (
        Profilo(
            "scoperta",
            "Chi è acceso? Nessuna scansione di porte.",
            ("-sn", "-T3"),
            False,
            "basso",
            "Primo passo su una rete nuova, prima di toccare qualunque porta.",
        ),
        Profilo(
            "rapido",
            "Le 100 porte TCP più comuni.",
            ("--top-ports", "100", "-T3"),
            False,
            "basso",
            "Colpo d'occhio su un host singolo. Gira anche senza root (connect scan).",
        ),
        Profilo(
            "tcp-completo",
            "Tutte le 65535 porte TCP.",
            ("-p-", "-T3", "--max-retries", "2"),
            False,
            "medio",
            "Quando il profilo rapido non basta e hai tempo. Su un /24 può durare ore.",
        ),
        Profilo(
            "servizi",
            "Versione dei servizi sulle prime 1000 porte.",
            ("-sV", "--version-intensity", "5", "--top-ports", "1000", "-T3"),
            False,
            "medio",
            "Dopo aver capito cosa è aperto. Parla con i servizi, quindi finisce nei loro log.",
        ),
        Profilo(
            "os",
            "Riconoscimento del sistema operativo.",
            ("-O", "--osscan-limit", "--top-ports", "100", "-T3"),
            True,
            "medio",
            "Serve root. Ha bisogno di almeno una porta aperta e una chiusa per essere affidabile.",
        ),
        Profilo(
            "udp-top",
            "Le 50 porte UDP più comuni.",
            ("-sU", "--top-ports", "50", "-T3"),
            True,
            "medio",
            "UDP è lento per natura: DNS, SNMP, NTP. Serve root.",
        ),
        Profilo(
            "script-sicuri",
            "Script NSE della categoria 'default and safe'.",
            ("--script", "default and safe", "--top-ports", "100", "-T3"),
            False,
            "medio",
            "Informazioni extra senza categorie intrusive. Verifica sempre cosa fa uno script prima.",
        ),
    )
}

# Flag che spostano il bersaglio fuori dal controllo dello scope, coinvolgono
# terze parti, o tolgono a nmap-cli il controllo dell'output.

# Opzioni lunghe: nmap le accetta anche con "=valore".
_LUNGHE: dict[str, str] = {
    "--excludefile": "le esclusioni si dichiarano nel file scope",
    "--exclude": "le esclusioni si dichiarano nel file scope",
    "--resume": "riprende una scansione che non è passata dallo scope",
    "--proxies": "instrada il traffico da terzi",
    "--script": "gli script si scelgono col profilo",
    "--script-args-file": "gli script si scelgono col profilo",
    "--datadir": "cambia i dati con cui nmap decide cosa fare",
    "--spoof-mac": "falsifica l'indirizzo MAC",
}

# Opzioni corte: nmap distingue maiuscole e minuscole (-sI è lo zombie, -si no)
# e accetta il valore attaccato (-oXfile), quindi si confronta per prefisso.
_CORTE: dict[str, str] = {
    "-iL": "legge target da file e aggira lo scope",
    "-iR": "sceglie target a caso su internet",
    "-sI": "idle scan: usa un host terzo come zombie",
    "-b": "FTP bounce: usa un server FTP terzo",
    "-D": "decoy: coinvolge indirizzi terzi",
    "-S": "falsifica l'indirizzo sorgente",
    "-sC": "attiva gli script 'default': per gli script c'è il profilo script-sicuri",
    "-A": "include -sC, quindi gli script 'default': per gli script c'è il profilo script-sicuri",
    "-oN": "l'output lo gestisce nmap-cli",
    "-oX": "l'output lo gestisce nmap-cli",
    "-oG": "l'output lo gestisce nmap-cli",
    "-oA": "l'output lo gestisce nmap-cli",
    "-oS": "l'output lo gestisce nmap-cli",
}


def filtra_extra(extra: list[str]) -> list[str]:
    """Rifiuta gli argomenti vietati. Non è una sandbox: vedi docs/04-profili.md."""
    for tok in extra:
        if not tok.startswith("-"):
            continue
        if tok.startswith("--"):
            nome = tok.split("=", 1)[0].lower()
            if nome in _LUNGHE:
                raise ArgomentoVietato(i18n.t("pr_vietato", flag=nome, motivo=_LUNGHE[nome]))
            continue
        for corto, motivo in _CORTE.items():
            if tok.startswith(corto):
                raise ArgomentoVietato(i18n.t("pr_vietato", flag=corto, motivo=motivo))
    return extra


# -- lingua -------------------------------------------------------------------
# Testi tradotti. L'italiano resta quello definito sopra.
_TR_PROFILI: dict[str, dict[str, list[str]]] = {
    "en": {
        "scoperta": ["Who is up? No port scan.", "First step on a new network, before touching any port."],
        "rapido": [
            "The 100 most common TCP ports.",
            "Quick look at a single host. Also runs without root (connect scan).",
        ],
        "tcp-completo": [
            "All 65535 TCP ports.",
            "When the rapido profile isn't enough and you have time. On a /24 it can take hours.",
        ],
        "servizi": [
            "Service versions on the top 1000 ports.",
            "Once you know what is open. It talks to the services, so it ends up in their logs.",
        ],
        "os": [
            "Operating system detection.",
            "Needs root. Needs at least one open and one closed port to be reliable.",
        ],
        "udp-top": ["The 50 most common UDP ports.", "UDP is slow by nature: DNS, SNMP, NTP. Needs root."],
        "script-sicuri": [
            "NSE scripts in the 'default and safe' category.",
            "Extra information without intrusive categories. Always check what a script does first.",
        ],
    },
    "zh": {
        "scoperta": ["哪些主机存活？不扫描端口。", "新网络上的第一步，在碰任何端口之前。"],
        "rapido": ["最常见的 100 个 TCP 端口。", "快速查看单个主机。无需 root 也能运行（connect 扫描）。"],
        "tcp-completo": [
            "全部 65535 个 TCP 端口。",
            "rapido 配置不够、且时间充裕时使用。扫一个 /24 可能要几个小时。",
        ],
        "servizi": [
            "前 1000 个端口上的服务版本。",
            "弄清哪些端口开放之后使用。会与服务交互，因此会留在它们的日志里。",
        ],
        "os": ["操作系统识别。", "需要 root。至少要有一个开放端口和一个关闭端口才可靠。"],
        "udp-top": ["最常见的 50 个 UDP 端口。", "UDP 天生就慢：DNS、SNMP、NTP。需要 root。"],
        "script-sicuri": [
            "'default and safe' 类别的 NSE 脚本。",
            "获取额外信息，不使用侵入性类别。使用前务必先确认脚本做了什么。",
        ],
    },
}
_TR_VIETATI: dict[str, dict[str, str]] = {
    "en": {
        "le esclusioni si dichiarano nel file scope": "exclusions are declared in the scope file",
        "riprende una scansione che non è passata dallo scope": "resumes a scan that did not go through the scope",
        "instrada il traffico da terzi": "routes traffic through third parties",
        "gli script si scelgono col profilo": "scripts are chosen through the profile",
        "cambia i dati con cui nmap decide cosa fare": "changes the data nmap uses to decide what to do",
        "falsifica l'indirizzo MAC": "spoofs the MAC address",
        "legge target da file e aggira lo scope": "reads targets from a file and bypasses the scope",
        "sceglie target a caso su internet": "picks random targets on the internet",
        "idle scan: usa un host terzo come zombie": "idle scan: uses a third-party host as a zombie",
        "FTP bounce: usa un server FTP terzo": "FTP bounce: uses a third-party FTP server",
        "decoy: coinvolge indirizzi terzi": "decoy: involves third-party addresses",
        "falsifica l'indirizzo sorgente": "spoofs the source address",
        "attiva gli script 'default': per gli script c'è il profilo script-sicuri": (
            "enables the 'default' scripts: for scripts use the script-sicuri profile"
        ),
        "include -sC, quindi gli script 'default': per gli script c'è il profilo script-sicuri": (
            "includes -sC, hence the 'default' scripts: for scripts use the script-sicuri profile"
        ),
        "l'output lo gestisce nmap-cli": "output is handled by nmap-cli",
    },
    "zh": {
        "le esclusioni si dichiarano nel file scope": "排除项在作用域文件中声明",
        "riprende una scansione che non è passata dallo scope": "会恢复一次未经作用域校验的扫描",
        "instrada il traffico da terzi": "通过第三方转发流量",
        "gli script si scelgono col profilo": "脚本通过配置选择",
        "cambia i dati con cui nmap decide cosa fare": "会改变 nmap 决定行为所依据的数据",
        "falsifica l'indirizzo MAC": "伪造 MAC 地址",
        "legge target da file e aggira lo scope": "从文件读取目标，绕过作用域",
        "sceglie target a caso su internet": "在互联网上随机选择目标",
        "idle scan: usa un host terzo come zombie": "idle 扫描：把第三方主机当作僵尸主机",
        "FTP bounce: usa un server FTP terzo": "FTP bounce：利用第三方 FTP 服务器",
        "decoy: coinvolge indirizzi terzi": "诱饵扫描：牵涉第三方地址",
        "falsifica l'indirizzo sorgente": "伪造源地址",
        "attiva gli script 'default': per gli script c'è il profilo script-sicuri": (
            "会启用 'default' 脚本：脚本请用 script-sicuri 配置"
        ),
        "include -sC, quindi gli script 'default': per gli script c'è il profilo script-sicuri": (
            "包含 -sC，也就是 'default' 脚本：脚本请用 script-sicuri 配置"
        ),
        "l'output lo gestisce nmap-cli": "输出由 nmap-cli 管理",
    },
}
_ORIGINALI = (PROFILI, _LUNGHE, _CORTE)


def applica_lingua(lingua: str) -> None:
    """Passa profili e motivi dei flag vietati alla lingua scelta. Ripartendo
    sempre dagli originali italiani, chiamarla più volte non accumula niente."""
    global PROFILI, _LUNGHE, _CORTE
    PROFILI, _LUNGHE, _CORTE = _ORIGINALI
    prof = _TR_PROFILI.get(lingua)
    if not prof:
        return
    PROFILI = {
        n: replace(p, descrizione=prof[n][0] or p.descrizione, quando=prof[n][1] or p.quando) if n in prof else p
        for n, p in PROFILI.items()
    }
    viet = _TR_VIETATI.get(lingua, {})
    _LUNGHE = {k: viet.get(v, v) for k, v in _LUNGHE.items()}
    _CORTE = {k: viet.get(v, v) for k, v in _CORTE.items()}
