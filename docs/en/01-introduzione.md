# Introduction

🌐 [Italiano](../01-introduzione.md) · **English** · [中文](../zh/01-introduzione.md)

This tool started as a pile of shell scripts I used to remember Nmap commands: discovery, port scanning, versions, NSE scripts. They were executable notes. They worked, but they had a flaw: one wrong variable at the top of the file and the scan went off against something that had nothing to do with the job.

`nmap-cli` removes that flaw. The scope becomes a file with a name, the signature of whoever authorizes it, and validity dates. You pick the target on the command line, and it is checked against that file before Nmap is even looked up in `PATH`.

## Three design decisions

**Dry-run is the default behavior.** Without `--esegui` the program prints the command and logs it. Starting by mistake is harder than not starting at all.

**When in doubt, refuse.** A target in an odd format, a CIDR that is one bit too wide, a hostname that resolves to an excluded address: all refused. The cost of a false refusal is fixing one line of scope. The cost of a false go-ahead is an incident.

**No dependencies.** Only the Python standard library. A tool that has to guarantee what it runs shouldn't drag along fifty packages you have to trust.

## What's in the repository

```
nmap-cli/
├── src/nmapcli/
│   ├── scope.py      loads the scope and decides whether a target is allowed
│   ├── profiles.py   the profiles and the forbidden-flag filter
│   ├── runner.py     builds the command and runs it (never through a shell)
│   ├── audit.py      hash-chained audit log
│   ├── firma.py      signs and verifies the scope with an SSH key
│   ├── rapporto.py   reads Nmap XML, generates reports and diffs them
│   └── cli.py        arguments, messages, exit codes
├── tests/            unittest, no network and no nmap
├── docs/             this documentation
├── examples/         example scopes
├── scripts/          the original shell cheatsheet the project grew out of
└── lab/              a Docker lab with deliberately vulnerable targets
```

## Who it's for

People who do security testing under contract and want a clean record of what they ran, when, and under which authorization. Students who want a healthy habit from day one: scope first, then the command. Team leads who want nobody typing `nmap` by hand against an IP pasted from a chat.

## Who it's not for

Anyone looking for a way to scan covertly. You won't find zombie scans, decoys, spoofing or fragmentation here: they are forbidden flags. Nmap has them, and anyone who really needs them on an authorized engagement knows where to find them.

## Where to go next

If this is your first security test, read [02-autorizzazione.md](02-autorizzazione.md) before anything else. If you only need to know how to write the scope, go to [03-scope.md](03-scope.md).
