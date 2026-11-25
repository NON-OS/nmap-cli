# Script

`nmap_workflow.sh` è il cheatsheet da cui è nato il progetto: i comandi Nmap in ordine di lavoro, con una nota su ogni comando che spiega perché e quando usarlo.

Non va eseguito così com'è. I target sono segnaposto (`<HOST_O_RETE>`) e molti comandi sono pensati per essere lanciati uno alla volta, leggendo il risultato del precedente. Per lanciare davvero una scansione usa `nmap-cli`, che controlla lo scope prima di partire.

## Cosa non copre il programma

Il cheatsheet include tecniche come la scansione zombie (`-sI`), i decoy (`-D`) e la frammentazione. `nmap-cli` le vieta di proposito: coinvolgono host terzi o servono a eludere il rilevamento, e hanno senso solo in un test concordato per iscritto con il cliente (per esempio per verificare un IDS). In quel caso usa nmap direttamente e annota la scelta nell'ingaggio.

Lo stesso vale per la sezione brute force / audit delle credenziali (gli script NSE della categoria `brute`: `ssh-brute`, `http-brute`, `smb-brute`, ecc.). Sono documentati qui come riferimento, con le note sui rischi — ma `nmap-cli` **non li esegue**: non c'è un profilo brute e la CLI non costruisce quei comandi. Sono `intrusive`, possono bloccare account e far scattare allarmi, e non passano dal controllo dello scope. Se ti servono per un audit autorizzato delle tue credenziali, lanci nmap a mano, con piena responsabilità di chi esegue.
