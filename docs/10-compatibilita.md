# Compatibilità e prove

🌐 **Italiano** · [English](en/10-compatibilita.md) · [中文](zh/10-compatibilita.md)

Questa pagina dice cosa è stato verificato contro nmap vero e cosa no. Non è un elenco di promesse.

**Versione provata:** nmap 7.993, installato con Homebrew su macOS arm64.

## Cosa è stato verificato

1. **I flag dei profili esistono.** Ogni flag usato da un profilo è stato cercato nell'help e nella pagina di manuale di nmap 7.993: nessuno sconosciuto.
2. **I flag vietati esistono.** Anche l'elenco dei vietati è stato confrontato. Due nomi erano inventati (`--proxy`, `--interactive`) e sono stati tolti. In senso opposto, `-sC` e `-A` attivavano gli script `default` aggirando il blocco di `--script`: ora sono vietati.
3. **Il lancio vero funziona.** `scoperta`, `rapido`, `servizi` e `script-sicuri` sono stati lanciati con `--esegui` su `127.0.0.1`; `rapporto` ha letto gli XML veri e `confronta` ha dato "Nessuna differenza" su due scansioni uguali.
4. **L'audit.** Dopo i lanci veri la catena risulta integra.
5. **Stdin chiuso.** Il processo figlio non eredita stdin. nmap legge target da stdin solo con `-iL -`, che è vietato, ma la regola vale comunque; c'è un test con un eseguibile finto.
6. **Python e installazione.** Test passati con Python 3.11.18 e 3.13 su macOS e con 3.12.3 su Linux. Installazione pulita con `pip install .` in un venv nuovo, comando nel PATH compreso.
7. **I tipi.** `mypy --strict` non trova errori in `src/`. Non è una prova di correttezza, ma un controllo in più su cosa un parametro o un ritorno può davvero essere; è nella CI, quindi non si guasta senza che un test lo segnali.
8. **Il binario giusto.** `doctor` e `--esegui` controllano che l'output di `--version` contenga davvero "Nmap version": nel PATH può finire un altro programma chiamato `nmap`. Provato con l'eseguibile vero (accettato) e con un finto che stampa un'altra stringa (rifiutato, codice 5, niente scritto nell'audit).
9. **I dati del bersaglio nei report.** Hostname, servizio e versione arrivano da ciò che il bersaglio risponde, non da chi lancia la scansione. `rapporto` toglie i caratteri di controllo (a capo compresi) e scappa i `|` prima di scriverli in un report di testo o Markdown, così un banner ostile non può iniettare una riga, un titolo o una colonna falsi. Provato con un hostname e una versione contenenti un a capo e una finta intestazione `## ...`: restano testo su una riga sola. Il dettaglio è in [08-rapporti.md](08-rapporti.md#hostname-servizi-e-versioni-sono-dati-del-bersaglio-non-testo-fidato).
10. **La CI stessa.** Le GitHub Action sono ancorate allo SHA del commit, non a un tag mobile come `@v4`: chi controlla il repo upstream di un'azione non può farla puntare altrove senza che il nostro workflow cambi riga. `ruff format --check` impedisce allo stile di derivare nel tempo. `coverage` misura quanto i test toccano davvero: la CI fallisce sotto l'85%, il valore reale è l'89%.

## Cosa NON è stato verificato

`os` e `udp-top` richiedono root e non sono stati eseguiti. `tcp-completo` non è stato lanciato per intero. I profili sono stati provati solo su `127.0.0.1`, quindi non so come si comportino su reti reali con firewall e rate limiting. Il rapporto non legge gli output degli script NSE.

## Se usi un'altra versione

I flag e il formato XML cambiano tra una versione e l'altra. Lancia `make check` e un lancio di prova su un bersaglio tuo prima di fidarti. Se trovi un flag che aggira lo scope e non è tra i vietati, è una vulnerabilità: vedi [SECURITY.md](../SECURITY.md).
