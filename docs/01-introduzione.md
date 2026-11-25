# Introduzione

🌐 **Italiano** · [English](en/01-introduzione.md) · [中文](zh/01-introduzione.md)

Questo strumento nasce da un mucchio di script shell che usavo per ricordarmi i comandi di Nmap: scoperta, scansione delle porte, versioni, script NSE. Erano appunti eseguibili. Funzionavano, ma avevano un difetto: bastava sbagliare una variabile in cima al file e la scansione partiva su qualcosa che non c'entrava.

`nmap-cli` toglie quel difetto. Lo scope diventa un file con nome, firma di chi autorizza e date di validità. Il target lo scegli a riga di comando e viene confrontato con quel file prima che Nmap venga nemmeno cercato nel `PATH`.

## Tre decisioni di progetto

**Il dry-run è il comportamento normale.** Senza `--esegui` il programma stampa il comando e lo registra. Partire per sbaglio è più difficile che non partire per niente.

**Nel dubbio si rifiuta.** Un target con un formato strano, un CIDR che sfora di un bit, un hostname che risolve in un indirizzo escluso: tutto rifiutato. Il costo di un falso rifiuto è dover correggere una riga di scope. Il costo di un falso via libera è un incidente.

**Nessuna dipendenza.** Solo la libreria standard di Python. Uno strumento che deve garantire cosa lancia non dovrebbe portarsi dietro cinquanta pacchetti da fidarsi.

## Cosa trovi nel repository

```
nmap-cli/
├── src/nmapcli/
│   ├── scope.py      carica lo scope e decide se un target è ammesso
│   ├── profiles.py   i profili e il filtro sui flag vietati
│   ├── runner.py     costruisce il comando e lo lancia (mai una shell)
│   ├── audit.py      registro a catena di hash
│   ├── firma.py      firma e verifica dello scope con una chiave SSH
│   ├── rapporto.py   legge l'XML di Nmap, genera i report e li confronta
│   └── cli.py        argomenti, messaggi, codici di uscita
├── tests/            unittest, senza rete e senza nmap
├── docs/             questa documentazione
├── examples/         scope d'esempio
├── scripts/          il cheatsheet shell originale, da cui è nato il progetto
└── lab/              un laboratorio Docker con bersagli volutamente vulnerabili
```

## A chi serve

A chi fa test di sicurezza su incarico e vuole una traccia pulita di cosa ha lanciato, quando e con quale autorizzazione. A chi studia e vuole un'abitudine sana fin dal primo giorno: prima lo scope, poi il comando. A chi ha un team e vuole che nessuno scriva un `nmap` a mano su un IP incollato da una chat.

## A chi non serve

A chi cerca un modo di scansionare di nascosto. Qui non troverai zombie scan, decoy, spoofing o frammentazione: sono flag vietati. Nmap li ha, e chi ne ha davvero bisogno su un incarico autorizzato sa dove trovarli.

## Da dove continuare

Se è la prima volta che fai un test di sicurezza, leggi [02-autorizzazione.md](02-autorizzazione.md) prima di ogni altra cosa. Se ti serve solo capire come si scrive lo scope, vai a [03-scope.md](03-scope.md).
