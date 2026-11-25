# Sicurezza

## Segnalare una vulnerabilità

Se trovi un modo di far passare un target fuori scope, di aggirare il filtro sui flag, o di falsificare il registro di audit senza che `nmap-cli audit` se ne accorga, apri una segnalazione privata dalla scheda Security del repository (Report a vulnerability). Non aprire una issue pubblica.

Cerco di rispondere entro una settimana. Se il problema è reale lo correggo e ti cito nel changelog, se vuoi.

## Cosa conta come vulnerabilità

- Un target che il controllo ammette ma che non è nello scope.
- Un flag vietato che arriva a Nmap.
- Un'esecuzione che parte senza conferma.
- Una modifica al registro che la verifica non rileva e che non rientra nei limiti già descritti in [docs/05-audit.md](docs/05-audit.md).

## Cosa non conta

- Il fatto che chi ha accesso al tuo terminale possa lanciare `nmap` direttamente.
- Il fatto che chi può riscrivere tutto il registro possa ricostruire la catena.
- Uno scope scritto male dall'utente.

Sono limiti noti e dichiarati.

## Abusi

Se vedi questo strumento usato per attaccare sistemi altrui, segnalalo allo stesso modo.
