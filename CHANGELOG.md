# Changelog

Il formato segue [Keep a Changelog](https://keepachangelog.com/it-IT/1.1.0/). Le versioni seguono [SemVer](https://semver.org/lang/it/).

## [Non rilasciato]

- Comando `guida`: modalità interattiva che porta passo per passo da scope a scansione (scope → profilo → target → anteprima → conferma), riusando lo stesso percorso di `scansiona`.
- Logo NONOS allo startup (su stderr, così non inquina mai stdout di `rapporto`/`confronta`).
- Istruzioni di installazione cross-platform: Kali/Debian (`apt`) oltre a macOS. README con posizionamento Kali/Parrot/Linux primario.
- `scripts/`: aggiunta al cheatsheet la sezione brute force / audit credenziali (script NSE `brute` di nmap), come riferimento con le note sui rischi di lockout e la raccomandazione `brute.firstonly`. È solo documentazione: la CLI non esegue il brute force e non ha un profilo per farlo.
- `docs/11-brute-force.md` (it/en/zh): spiega perché `nmap-cli` non automatizza il brute force e come fare un audit delle credenziali a mano, sotto autorizzazione. Collegata dall'indice dei README e da `04-profili.md`.

## [0.3.0] - 2026-11-23

- Scope firmato con chiavi SSH: `scope-firma`, `scope-verifica`, `--firmatari`. Firmatario e impronta nell'audit.
- Vietati `-sC` e `-A`: attivavano gli script `default` aggirando `--script`. Tolti due nomi vietati che non esistevano.
- Lo stdin del processo figlio è chiuso.
- `doctor` e `--esegui` controllano che il binario nel PATH sia davvero nmap, non un omonimo.
- `rapporto`: hostname, servizio e versione (dati del bersaglio, non dell'operatore) non possono più iniettare una riga, un titolo o una colonna falsi in un report di testo o Markdown.
- Corretti i tipi segnalati da `mypy --strict`; il controllo è ora nella CI e in `make check`.
- Test passati con Python 3.11.18 e 3.13 su macOS e con 3.12.3 su Linux; installazione pulita con `pip install .`.
- Le GitHub Action sono ancorate allo SHA del commit, non a un tag mobile; aggiunto `ruff format --check`.
- Copertura dei test misurata con `coverage`: la CI fallisce sotto l'85% (reale: 89%).
- Pagina `docs/10-compatibilita.md` con ciò che è stato provato con nmap 7.993.

## [0.2.0]

- Comando `rapporto`: dall'XML di nmap a testo, Markdown o JSON.
- Comando `confronta`: differenze tra due scansioni (host, porte, versioni), con `--exit-code` per la CI.
- CI su Linux e macOS con Python 3.11, 3.12 e 3.13, più lint con ruff.
- Template per issue e pull request, codice di condotta, dependabot, Makefile.
- Il cheatsheet shell originale è in `scripts/`.

## [0.1.0]

Prima versione.

- Controllo dello scope da file TOML: IP, CIDR, hostname, wildcard, esclusioni, date di validità.
- Dry-run di default; `--esegui` richiede conferma.
- Sette profili di scansione e filtro sui flag vietati.
- Registro di audit a catena di hash e comando `audit` per verificarlo.
- Comandi `init`, `verifica`, `profili`, `doctor`.
- Lab Docker con due bersagli vulnerabili.
