# Autorizzazione

🌐 **Italiano** · [English](en/02-autorizzazione.md) · [中文](zh/02-autorizzazione.md)

Una scansione senza permesso non diventa legittima perché è andata bene. Questa pagina spiega cosa serve prima, chi può darlo, e dove puoi allenarti senza chiedere niente a nessuno.

## Chi può autorizzare

Solo chi ha il controllo del sistema. Il tuo responsabile non basta se i server sono di un cliente. Il referente tecnico del cliente non basta se i server stanno da un cloud provider e il contratto del provider vieta i test. Spesso le autorizzazioni sono due: quella del proprietario dei dati e quella di chi ospita l'infrastruttura.

## Cosa deve dire il documento

```mermaid
flowchart TD
    D[Documento di autorizzazione] --> W[Chi: nome, ruolo, potere di firma]
    D --> T[Cosa: target in forma esatta]
    D --> Q[Quando: data di inizio e di fine, fasce orarie]
    D --> H[Come: attività consentite e vietate]
    D --> C[Contatto: chi chiamare se qualcosa si rompe]
    T --> S[(scope.toml)]
    Q --> S
    W --> S
```

Ogni campo del documento ha un posto nel file di scope. Se non riesci a compilare un campo, quel pezzo di autorizzazione manca.

Un punto che si trascura: "attività consentite". Una scansione completa di tutte le porte su un impianto industriale, o su una stampante di rete vecchia, può bloccare il dispositivo. Se il cliente ha sistemi fragili, scrivilo nel documento e usa il profilo `rapido` o `scoperta`.

## Prima di lanciare

Una lista breve, da leggere ogni volta:

1. Ho il documento firmato e lo posso ritrovare tra sei mesi.
2. Il file di scope dice le stesse cose del documento, non una versione più comoda.
3. Le date sono ancora valide.
4. So chi chiamare se un servizio smette di rispondere.
5. Sto usando il profilo meno rumoroso che mi serve.

## Dove allenarsi senza chiedere

| Dove | Note |
|---|---|
| Il lab di questo repo | Container tuoi su una rete locale. Vedi [07-lab.md](07-lab.md). |
| Macchine virtuali tue | VirtualBox, UTM, qualsiasi hypervisor, rete host-only. |
| `scanme.nmap.org` | Messo a disposizione dal progetto Nmap. Poche scansioni, niente di aggressivo. Controlla la policy sul sito. |
| Hack The Box, TryHackMe | Dentro le regole della piattaforma, solo sulle macchine assegnate. |
| Bug bounty | Solo i target dello scope del programma, e rispetta la lista delle attività vietate. |

Una nota su `scanme.nmap.org`: è un servizio gratuito offerto da un progetto open source. Trattalo come tratteresti il bagno di un amico, usalo senza lasciare il segno.

## Cosa fare se sbagli

Succede. Un indirizzo incollato male, una rete che si è rivelata essere di un altro.

1. Ferma la scansione (Ctrl-C).
2. Non cancellare niente: il registro di audit è la tua prova di buona fede e dice esattamente cosa è stato lanciato.
3. Avvisa subito il referente del cliente, o il proprietario del sistema se non è il cliente. Meglio una telefonata imbarazzante oggi che una denuncia dopo.
4. Scrivi cosa è successo mentre lo ricordi.

## Un'ultima cosa

Il file di scope è una dichiarazione tua, non una prova. Nessun programma può sapere se hai davvero il permesso. Se scrivi nello scope un indirizzo che non ti è stato assegnato, `nmap-cli` lo scansionerà e nel registro ci sarà il tuo nome accanto.
