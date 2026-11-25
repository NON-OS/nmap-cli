# Why nmap-cli does not do brute force

🌐 [Italiano](../11-brute-force.md) · **English** · [中文](../zh/11-brute-force.md)

`nmap-cli` does not try to guess credentials, and there is no profile that does. This is not a gap: it is a choice, the same line the tool holds everywhere else. This page explains why, and how to run a credential audit when you genuinely need one — by hand, with the responsibility on whoever runs it.

## The difference between finding and forcing

Everything `nmap-cli` does is *observe*: which hosts are up, which ports are open, which services and versions answer. With a correct scope and a cautious profile, these operations leave little behind and do not change the target's state.

Brute force is a different thing. The NSE scripts in the `brute` category (`ssh-brute`, `http-brute`, `smb-brute`, and the rest) send *real* login attempts, many of them, one after another. They do not read the system: they get in, or they try to. The consequences are of a different kind:

- **Lockout.** After N failed attempts many systems lock the account. The lock does not clear by itself, and if you aimed at the wrong user — a real, production account — you have caused an outage for someone who has nothing to do with the test.
- **Noise.** Hundreds of failed logins fill the logs and trip the IDS and the SOC. Passive enumeration goes unnoticed; brute force does not, by definition.
- **Fragility.** A misconfigured or loaded service can degrade or fall under the burst of requests.
- **Legal exposure.** Attempting to authenticate against a system you were not explicitly authorized to test that way is, in many jurisdictions, a separate offense from a plain scan.

## Why we do not automate it

The principle behind the whole tool is that an action with real consequences must never start by inertia. The scope is signed, dry-run is the default, every run lands in the audit log. An engine that, given a scan, maps open services to their `brute` scripts on its own and chains them does the exact opposite: it turns a grave decision — "I am about to try to break the authentication of these systems" — into a side effect of a command. That is how a mistake becomes an incident.

There is a technical reason too. The rest of `nmap-cli` never builds a command line by hand and never passes a string to a shell: the flag filter and the argument list are there for this. A brute engine has to pass `--script-args` (userdb, passdb, thresholds, timeouts), which is exactly the kind of string the rest of the code keeps out with care. Bringing it back inside the tool would bring back the risk the tool was built to avoid.

Finally, a reason of honesty. The README says, in three languages, that `nmap-cli` does not run brute force. It is a promise that makes the tool defensible to anyone who examines it. As long as it is true, it holds.

## How to do it, when you really need to

Credential brute force has a place in an audit: checking that a service does not accept weak passwords, that lockout policies work, that a default account was not left enabled. It is a legitimate activity — on your own systems, in a lab, or under written authorization that **explicitly** covers credential testing, not just scanning.

In that case you run Nmap directly. It is one line away, and it should stay an explicit choice:

```sh
nmap -p 22 --script ssh-brute \
  --script-args "userdb=users.txt,passdb=pass.txt,brute.firstonly=true,brute.threads=2,brute.delay=5,unpwdb.timelimit=10m" \
  192.0.2.10
```

A few precautions that reduce the harm:

- **`brute.firstonly=true`** stops the moment it finds the first valid credential, instead of keeping on hammering the account.
- Low **`brute.delay`** and **`brute.threads`** spread the attempts out: less noise, less lockout risk.
- **`unpwdb.timelimit`** caps the total time, so the operation ends within a known window.
- **Your own lists** (`userdb`/`passdb`): knowing exactly what you are trying is part of the audit. Without them, Nmap uses its default lists.
- **Scope first.** Validate the target with `nmap-cli verifica`, or check the scope file by hand, before launching anything. Nmap, run this way, does not do it for you.

The cheatsheet in [scripts/nmap_workflow.sh](../../scripts/nmap_workflow.sh) collects the most common `brute` scripts (SSH, FTP, HTTP, HTTP form, SMB, MySQL, Oracle, MongoDB) with a note on the risks of each and the full list of `brute` library options. It is reference material: you run the commands yourself, by hand, reading what they do before you execute them.

## In short

| | |
|---|---|
| Does `nmap-cli` automate brute force? | No, on purpose. There is no profile, the CLI does not build those commands. |
| Can I still do it? | Yes, with `nmap` directly, on your own responsibility and with written authorization. |
| Where are the commands? | In the cheatsheet, [scripts/nmap_workflow.sh](../../scripts/nmap_workflow.sh), as reference. |
| Why this choice? | A credential attack is a decision, not an automatic step in a pipeline. |

The detail on the flags `nmap-cli` blocks, and why the filter is not a sandbox, is in [04-profili.md](04-profili.md).
