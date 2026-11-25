#!/usr/bin/env bash
# nmap_workflow_v3.sh
# Cheatsheet operativo completo. Solo ambienti autorizzati.
# Le note sotto ogni comando spiegano il perché e il quando, non solo il cosa.

TARGET="<HOST_O_RETE>"
SUBNET="<RETE>/<CIDR>"
ZOMBIE="<HOST_ZOMBIE>"
OUT="<PREFISSO_OUTPUT>"

# ---------------------------------------------------------------
# Scoperta host
# ---------------------------------------------------------------

# Su LAN l'ARP non si può bloccare: se un device non risponde all'ARP,
# non comunica affatto. L'ICMP invece molti IoT lo ignorano.
nmap -sn "$SUBNET"

# Senza reverse DNS. Su /24 la differenza si sente.
nmap -sn -n "$SUBNET"

# Ping TCP: SYN su porte comuni. RST = vivo, SYN/ACK = vivo e porta aperta.
nmap -sn -PS22,80,443 "$SUBNET"

# Ping ACK. Se il firewall è stateful l'ACK viene scartato e l'host
# risulta morto anche se è vivo. Serve più a capire che firewall
# ho davanti che a trovare host.
nmap -sn -PA80,443 "$SUBNET"

# UDP verso DNS e SNMP. Lento, ma a volte è l'unica cosa che passa.
nmap -sn -PU53,161 "$SUBNET"

# Tre probe ICMP diversi. Se ne passa uno, ho l'host.
nmap -sn -PE -PP -PM "$SUBNET"

# ARP puro. Solo subnet locale, non attraversa router.
nmap -sn -PR "$SUBNET"

# Ping a livello IP: protocolli 1 (ICMP), 6 (TCP), 17 (UDP).
nmap -sn -PO1,6,17 "$SUBNET"

# List scan: risolve i nomi DNS senza mandare un solo pacchetto
# al target. Utile per mappare una rete senza toccarla.
nmap -sL "$SUBNET"

# ---------------------------------------------------------------
# Scansione porte
# ---------------------------------------------------------------

# SYN scan completo. Richiede root. Il default quando posso.
sudo nmap -sS -p- -T4 "$TARGET"

# Solo porte note. Quando ho fretta o il target è delicato.
sudo nmap -sS -p 1-1024 -T4 "$TARGET"

# Connect scan. Niente root, ma il target vede la connessione completa
# e nei log dell'applicazione resta tutto. Più rumoroso di -sS.
nmap -sT --top-ports 1000 "$TARGET"

# UDP. Senza questo metà dei servizi reali non li vedi.
# Lento per natura: nessun handshake, solo timeout.
sudo nmap -sU --top-ports 50 "$TARGET"

# --- Stealth: funzionano solo su stack che rispettano RFC 793 ---
# Su Windows qualsiasi pacchetto malformato prende RST, quindi queste
# scansioni dicono "tutto chiuso" e non valgono niente.
sudo nmap -sN -p 22,80,443 "$TARGET"     # Null: nessun flag
sudo nmap -sF -p 22,80,443 "$TARGET"     # FIN
sudo nmap -sX -p 22,80,443 "$TARGET"     # Xmas: FIN+PSH+URG

# ACK scan. Non dice se la porta è aperta. Dice se il firewall è stateful:
#   stateless -> ACK passa -> RST -> unfiltered
#   stateful  -> ACK scartato -> silenzio -> filtered
# È la prima cosa che lancio quando voglio capire che firewall ho davanti.
sudo nmap -sA -p 1-1000 "$TARGET"

# Window scan. Si basa sulla dimensione della finestra nel RST.
# Stack moderni normalizzano o randomizzano, quindi oggi è inaffidabile.
sudo nmap -sW -p 1-1000 "$TARGET"

# Maimon. Variante FIN/ACK, stessa fragilità.
sudo nmap -sM -p 22,80,443 "$TARGET"

# Idle scan. Non manda un solo pacchetto dal mio IP.
# Meccanica corretta: Nmap manda un SYN spoofato (sorgente = zombie)
# al target. Se la porta è APERTA, il target risponde SYN/ACK allo
# zombie. Lo zombie non se lo aspetta e risponde RST -> IPID +1.
# Se la porta è CHIUSA, il target risponde RST allo zombie, che lo
# ignora -> IPID non cambia. Se è FILTRATA, silenzio -> IPID non cambia.
# Quindi: delta 0 = closed|filtered; delta > 0 = open.
# Nmap manda più probe per confermare, quindi il delta totale può
# essere >1. Non è "delta 1 per probe" in modo rigido: è "ogni
# SYN/ACK che arriva allo zombie genera un RST e quindi +1".
sudo nmap -sI "$ZOMBIE" "$TARGET"

# Scansione protocolli IP (non porte). Numeri di protocollo:
# 1=ICMP, 6=TCP, 17=UDP.
nmap -sO -p 1-255 "$TARGET"

# SCTP INIT scan. Equivalente SYN per SCTP. Protocollo telecom,
# ma supportato da Nmap e utile per completezza.
sudo nmap -sY -p 22,80 "$TARGET"

# SCTP cookie-echo. Variante più stealth dell'INIT.
nmap -sZ -p 22,80 "$TARGET"

# FTP bounce scan. Tecnica storica: usa un server FTP come proxy
# per aprire connessioni verso terzi. Praticamente disabilitata
# ovunque dal 2000 in poi. Serve per capire vecchie CVE, non per
# uso operativo reale.
nmap -b anonymous:anon@<FTP_RELAY> "$TARGET"

# ---------------------------------------------------------------
# Versioni dei servizi
# ---------------------------------------------------------------

nmap -sV -p 22,80,443,8080 "$TARGET"

# Intensità 0: solo banner, quasi nessun probe.
nmap -sV --version-intensity 0 "$TARGET"

# Intensità 9: tutti i probe. Lento ma massima precisione.
nmap -sV --version-intensity 9 "$TARGET"

# Equivalente esplicito a intensità massima.
nmap -sV --version-all "$TARGET"

# ---------------------------------------------------------------
# OS fingerprint
# ---------------------------------------------------------------

sudo nmap -O "$TARGET"

# Scan completo per avere per forza una porta aperta e una chiusa.
sudo nmap -O -p- "$TARGET"

# Match debole: mostra le ipotesi migliori. "(JUST GUESSING)"
# significa che la percentuale NON è una probabilità, è la quota
# di test del fingerprint che ha combaciato.
sudo nmap -O --osscan-guess "$TARGET"

# Salta l'OS detection sugli host senza coppia aperta/chiusa.
sudo nmap -O --osscan-limit "$TARGET"

# ---------------------------------------------------------------
# NSE
# Gli script non sono sandboxed. Uno script "intrusive" può
# modificare dati o far crashare un servizio.
#
# Categorie complete (non solo intrusive/dos/exploit):
# auth, broadcast, brute, default, discovery, dos, exploit,
# external, fuzzer, intrusive, malware, safe, version, vuln.
# Un script può appartenere a più categorie.
# ---------------------------------------------------------------

# Default. Sicuri, informativi, girano anche con -A.
nmap -sC "$TARGET"

# Solo vuln marcati "safe". Non toccano niente.
nmap --script "vuln and safe" -p 80,443 "$TARGET"

# Tutti i vuln. Include gli intrusivi. Da evitare su produzione.
nmap --script vuln "$TARGET"

# Credenziali deboli.
nmap --script auth "$TARGET"

# Scoperta servizi e info aggiuntive.
nmap --script discovery "$TARGET"

# Esclusione esplicita delle categorie pericolose.
nmap --script "not intrusive and not dos and not exploit" "$TARGET"

# Enumeration HTTP.
nmap --script http-enum,http-headers,http-methods -p 80,443 "$TARGET"

# EternalBlue.
nmap --script smb-vuln-ms17-010 -p 445 "$TARGET"

# Heartbleed.
nmap --script ssl-heartbleed -p 443 "$TARGET"

# Brute force SNMP.
nmap --script snmp-brute -sU -p 161 "$TARGET"

# Prima di lanciare uno script guardo le categorie.
# La sintassi corretta per esplorare una categoria intera è:
nmap --script-help "category:discovery"

# Per un singolo script:
nmap --script-help <NOME_SCRIPT>

# ---------------------------------------------------------------
# Evasione / test firewall
# ---------------------------------------------------------------

# Frammentazione IP. Solo firewall stateless o molto vecchi.
sudo nmap -f -p 80,443 "$TARGET"

# MTU personalizzato.
sudo nmap --mtu 16 -p 80,443 "$TARGET"

# Porta sorgente 53. Sfrutta regole "allow DNS" mal configurate.
# Oggi è raro, ma su apparati legacy capita.
sudo nmap -g 53 -p 80,443 "$TARGET"

# Padding: byte casuali per cambiare la firma del pacchetto.
sudo nmap --data-length 32 -T2 "$TARGET"

# Decoy. Mescola il mio IP a 10 casuali.
sudo nmap -D RND:10,ME "$TARGET"

# MAC spoofing. Utile solo sullo stesso segmento L2.
sudo nmap --spoof-mac 0 "$TARGET"

# Checksum invalido. Un host normale scarta in silenzio.
# Se ricevo risposta c'è un middlebox che non verifica il checksum.
sudo nmap --badsum -p 80,443 "$TARGET"

# Ordine casuale degli host.
sudo nmap --randomize-hosts "$SUBNET"

# ---------------------------------------------------------------
# Timing
# ---------------------------------------------------------------

# Paranoid: 5 minuti tra un probe. Nella pratica quasi mai usato.
nmap -T0 "$TARGET"

# Polite: 0.4s tra probe, circa 10x più lento del default.
nmap -T2 "$TARGET"

# Aggressive. Il compromesso giusto.
nmap -T4 "$TARGET"

# Rate minimo forzato. Utile su reti veloci, pericoloso su link congestionati.
nmap -T4 --min-rate 5000 --max-retries 2 "$TARGET"

# Rate massimo. Cap esplicito.
nmap -T4 --max-rate 1000 "$TARGET"

# Delay fisso.
nmap --scan-delay 1s "$TARGET"

# Timeout per host. Le porte a metà scan finiscono come "filtered".
nmap --host-timeout 90s "$TARGET"

# ---------------------------------------------------------------
# Output
# ---------------------------------------------------------------

nmap -sV -sC -oA "$OUT" "$TARGET"
nmap -sV -oN "$OUT.nmap" "$TARGET"
nmap -sV -oX "$OUT.xml" "$TARGET"
nmap -sV -oG "$OUT.gnmap" "$TARGET"

# --reason mostra il motivo di ogni stato.
nmap -sV --reason -v "$TARGET"

# --open mostra solo le porte aperte. Sembra banale, ma su scan
# grandi è la differenza tra output leggibile e caos.
nmap --open -sV "$TARGET"

# --proxies instrada la scansione attraverso proxy SOCKS4/HTTP.
# Funziona principalmente sulle connect scan (-sT).
nmap -sT --proxies socks4://<PROXY>:1080 "$TARGET"

# ---------------------------------------------------------------
# Scansioni combinate
# ---------------------------------------------------------------

sudo nmap -A -T4 -p- "$TARGET"
sudo nmap -sS -sV -O -sC -p- -T4 --osscan-guess -oA "$OUT" "$TARGET"
sudo nmap -sS -sU -sV -O -p- --top-ports 100 -T4 "$TARGET"

# ---------------------------------------------------------------
# Brute force / audit delle credenziali (NSE, categoria "brute")
# ---------------------------------------------------------------
# ATTENZIONE: questi script sono INTRUSIVE. Provano a indovinare le
# credenziali inviando molti tentativi di login veri. Possono:
#   - bloccare gli account (lockout) dopo N tentativi falliti,
#   - riempire i log e far scattare allarmi IDS/SOC,
#   - degradare o far cadere un servizio fragile.
# Il lockout NON si annulla da solo, e su un account sbagliato le
# conseguenze sono reali, anche legali. Usarli SOLO su sistemi tuoi,
# in un lab, o con autorizzazione scritta che preveda esplicitamente
# il brute force sulle credenziali.
#
# NIENTE di tutto questo passa dal controllo dello scope di nmap-cli:
# qui si lancia nmap a mano, con piena responsabilità di chi esegue.
#
# userdb/passdb sono due file di testo (un valore per riga). Senza,
# nmap usa le sue liste di default. Per ridurre il danno:
# brute.firstonly=true (ferma alla prima valida) e brute.delay.

# SSH.
nmap -p 22 --script ssh-brute \
  --script-args userdb=users.txt,passdb=pass.txt,brute.firstonly=true,ssh-brute.timeout=4s \
  "$TARGET"

# FTP.
nmap -p 21 --script ftp-brute \
  --script-args userdb=users.txt,passdb=pass.txt,brute.firstonly=true \
  "$TARGET"

# HTTP con autenticazione standard (Basic/Digest/NTLM).
# http-brute.path = la directory protetta da testare.
nmap -p 80 --script http-brute \
  --script-args http-brute.path=/admin,userdb=users.txt,passdb=pass.txt \
  "$TARGET"

# Form di login HTTP. Più delicato: deve indovinare i nomi dei campi.
# Se l'autodetection fallisce, uservar/passvar si mettono a mano.
nmap -p 80 --script http-form-brute \
  --script-args "http-form-brute.path=/login,http-form-brute.uservar=username,http-form-brute.passvar=password,userdb=users.txt,passdb=pass.txt" \
  "$TARGET"

# SMB. Enumera gli utenti prima di testare le password e salva le
# combinazioni valide nel registry di nmap per gli altri script smb-*.
nmap -p 445 --script smb-brute \
  --script-args userdb=users.txt,passdb=pass.txt \
  "$TARGET"

# MySQL. Le credenziali trovate finiscono nel registry: gli altri
# script mysql-* le riusano.
nmap -p 3306 --script mysql-brute \
  --script-args userdb=users.txt,passdb=pass.txt \
  "$TARGET"

# Oracle. Serve il SID. ATTENZIONE: lo script non conosce la soglia
# di lockout del database, quindi può bloccare molti account.
nmap -p 1521 --script oracle-brute \
  --script-args oracle-brute.sid=ORCL,userdb=users.txt,passdb=pass.txt \
  "$TARGET"

# MongoDB. Prima verifica se l'autenticazione è richiesta: se non lo
# è, risponde "No authentication needed" e non prova nulla.
nmap -p 27017 --script mongodb-brute \
  --script-args userdb=users.txt,passdb=pass.txt \
  "$TARGET"

# ---------------------------------------------------------------
# Opzioni globali della libreria "brute"
# Valgono per tutti gli script qui sopra, passate in --script-args.
# ---------------------------------------------------------------
#   brute.firstonly=true   ferma al primo successo (consigliato)
#   brute.delay=5          secondi tra un tentativo e il successivo
#   brute.threads=4        tentativi in parallelo (default variabile)
#   brute.guesses=100      numero massimo di tentativi totali
#   brute.passonly=true    username fisso, prova solo le password
#   brute.useraspass=true  prova anche username == password
#   brute.emptypass=true   prova anche la password vuota
#   brute.retries=2        quante volte ritentare un errore di rete
#   unpwdb.timelimit=10m   tempo massimo per l'intera operazione
#   unpwdb.passlimit=5000  tetto al numero di password usate
#
# Esempio prudente: pochi thread, delay, stop al primo successo,
# limite di tempo. Il minimo rumore possibile per un audit.
nmap -p 22 --script ssh-brute \
  --script-args "userdb=users.txt,passdb=pass.txt,brute.firstonly=true,brute.threads=2,brute.delay=5,unpwdb.timelimit=10m" \
  "$TARGET"
