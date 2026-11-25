# Perché nmap-cli non fa brute force

🌐 **Italiano** · [English](en/11-brute-force.md) · [中文](zh/11-brute-force.md)

`nmap-cli` non prova a indovinare credenziali, e non esiste un profilo che lo faccia. Non è una lacuna: è una scelta, ed è la stessa riga che il tool tiene su tutto il resto. Questa pagina spiega il perché, e come si fa un audit delle credenziali quando serve davvero, a mano, con la responsabilità in capo a chi lo esegue.

## La differenza tra scoprire e forzare

Tutto quello che fa `nmap-cli` è *osservare*: quali host sono attivi, quali porte sono aperte, quali servizi e versioni rispondono. Sono operazioni che, con uno scope corretto e un profilo prudente, lasciano poco dietro di sé e non cambiano lo stato del bersaglio.

Il brute force è un'altra cosa. Gli script NSE della categoria `brute` (`ssh-brute`, `http-brute`, `smb-brute`, e gli altri) inviano tentativi di login *veri*, molti, uno dopo l'altro. Non leggono il sistema: ci entrano, o ci provano. Le conseguenze sono di natura diversa:

- **Lockout.** Dopo N tentativi falliti molti sistemi bloccano l'account. Il blocco non si annulla da solo, e se hai preso di mira l'utente sbagliato — un account reale, di produzione — hai causato un disservizio a qualcuno che non c'entra.
- **Rumore.** Centinaia di login falliti riempiono i log e fanno scattare gli allarmi dell'IDS e del SOC. Un'enumerazione passiva passa inosservata; un brute force no, per definizione.
- **Fragilità.** Un servizio mal configurato o sotto carico può degradare o cadere sotto la raffica di richieste.
- **Responsabilità legale.** Tentare di autenticarsi su un sistema che non ti è stato esplicitamente autorizzato per quello è, in molte giurisdizioni, un reato a sé, distinto dalla semplice scansione.

## Perché non lo automatizziamo

Il principio di tutto il tool è che un'azione con conseguenze reali non deve mai partire per inerzia. Lo scope si firma, il dry-run è il default, ogni lancio finisce nell'audit. Un motore che, data una scansione, mappa da solo i servizi aperti ai relativi script `brute` e li lancia in catena fa l'esatto contrario: trasforma una decisione grave — "sto per tentare di sfondare l'autenticazione di questi sistemi" — in un effetto collaterale di un comando. È così che un errore diventa un incidente.

C'è anche una ragione tecnica. Il resto di `nmap-cli` non costruisce mai una riga di comando a mano e non passa mai una stringa a una shell: il filtro dei flag e la lista di argomenti servono a questo. Un brute engine deve passare `--script-args` (userdb, passdb, soglie, timeout), cioè proprio il tipo di stringa che il resto del codice tiene fuori con cura. Reintrodurlo dentro il tool significherebbe reintrodurre il rischio che il tool è nato per evitare.

Infine, una ragione di onestà. Il README dice, in tre lingue, che `nmap-cli` non esegue brute force. È una promessa che rende lo strumento difendibile davanti a chiunque lo esamini. Finché è vera, vale.

## Come si fa, quando serve davvero

Il brute force sulle credenziali ha senso in un audit: verificare che un servizio non accetti password deboli, che le politiche di lockout funzionino, che un account di default non sia rimasto attivo. È un'attività legittima — su sistemi tuoi, in un lab, o con un'autorizzazione scritta che preveda **esplicitamente** il test delle credenziali, non solo la scansione.

In quel caso si lancia Nmap direttamente. È a una riga di distanza, e deve restare una scelta esplicita:

```sh
nmap -p 22 --script ssh-brute \
  --script-args "userdb=users.txt,passdb=pass.txt,brute.firstonly=true,brute.threads=2,brute.delay=5,unpwdb.timelimit=10m" \
  192.0.2.10
```

Alcune accortezze che riducono il danno:

- **`brute.firstonly=true`** ferma allo stesso momento in cui trova la prima credenziale valida, invece di continuare a bersagliare l'account.
- **`brute.delay`** e **`brute.threads`** bassi diluiscono i tentativi: meno rumore, meno rischio di lockout.
- **`unpwdb.timelimit`** mette un tetto al tempo complessivo, così l'operazione finisce in un intervallo noto.
- **Liste tue** (`userdb`/`passdb`): sapere esattamente cosa stai provando è parte dell'audit. Senza, Nmap usa le sue liste di default.
- **Prima lo scope.** Valida il target con `nmap-cli verifica` o controlla lo scope file a mano prima di lanciare qualsiasi cosa. Nmap, lanciato così, non lo fa per te.

Il cheatsheet in [scripts/nmap_workflow.sh](../scripts/nmap_workflow.sh) raccoglie gli script `brute` più comuni (SSH, FTP, HTTP, HTTP form, SMB, MySQL, Oracle, MongoDB) con una nota sui rischi di ciascuno e l'elenco completo delle opzioni della libreria `brute`. È materiale di riferimento: i comandi li lanci tu, a mano, leggendo cosa fanno prima di eseguirli.

## In breve

| | |
|---|---|
| `nmap-cli` automatizza il brute force? | No, di proposito. Non c'è un profilo, la CLI non costruisce quei comandi. |
| Posso farlo lo stesso? | Sì, con `nmap` diretto, sotto la tua responsabilità e con autorizzazione scritta. |
| Dove trovo i comandi? | Nel cheatsheet, [scripts/nmap_workflow.sh](../scripts/nmap_workflow.sh), come riferimento. |
| Perché questa scelta? | Un attacco alle credenziali è una decisione, non un passo automatico di una pipeline. |

Il dettaglio sui flag che `nmap-cli` blocca, e sul perché il filtro non è una sandbox, è in [04-profili.md](04-profili.md).
