# Compatibility and testing

🌐 [Italiano](../10-compatibilita.md) · **English** · [中文](../zh/10-compatibilita.md)

This page states what has and hasn't been verified against real nmap. It isn't a list of promises.

**Version tested:** nmap 7.993, installed with Homebrew on macOS arm64.

## What has been verified

1. **The profile flags exist.** Every flag used by a profile was looked up in the help output and the man page of nmap 7.993: none unknown.
2. **The forbidden flags exist.** The forbidden list was checked too. Two names were made up (`--proxy`, `--interactive`) and have been removed. In the other direction, `-sC` and `-A` enabled the `default` scripts, bypassing the `--script` block: they are now forbidden.
3. **Real runs work.** `scoperta`, `rapido`, `servizi` and `script-sicuri` were run with `--esegui` against `127.0.0.1`; `rapporto` read the real XML files and `confronta` returned "Nessuna differenza" (no differences) on two identical scans.
4. **The audit log.** After the real runs the chain is intact.
5. **Stdin closed.** The child process doesn't inherit stdin. nmap reads targets from stdin only with `-iL -`, which is forbidden, but the rule applies anyway; there's a test with a fake executable.
6. **Python and installation.** Tests pass with Python 3.11.18 and 3.13 on macOS and with 3.12.3 on Linux. Clean install with `pip install .` in a fresh venv, command on the PATH included.
7. **Types.** `mypy --strict` finds no errors in `src/`. It isn't proof of correctness, but an extra check on what a parameter or return value can actually be; it runs in CI, so it can't break without a test flagging it.
8. **The right binary.** `doctor` and `--esegui` check that the output of `--version` really contains "Nmap version": some other program called `nmap` could end up on the PATH. Tested with the real executable (accepted) and with a fake one printing a different string (refused, code 5, nothing written to the audit log).
9. **Target data in reports.** Hostname, service and version come from what the target answers, not from whoever runs the scan. `rapporto` strips control characters (newlines included) and escapes `|` before writing them into a text or Markdown report, so a hostile banner can't inject a fake row, heading or column. Tested with a hostname and a version containing a newline and a fake `## ...` heading: they stay text on a single line. Details in [08-rapporti.md](08-rapporti.md#hostnames-services-and-versions-are-target-data-not-trusted-text).
10. **CI itself.** GitHub Actions are pinned to the commit SHA, not to a moving tag like `@v4`: whoever controls an action's upstream repo can't repoint it without a line of our workflow changing. `ruff format --check` keeps the style from drifting over time. `coverage` measures how much the tests actually exercise: CI fails below 85%, the actual figure is 89%.

## What has NOT been verified

`os` and `udp-top` require root and were not run. `tcp-completo` wasn't run to completion. The profiles were tested only against `127.0.0.1`, so I don't know how they behave on real networks with firewalls and rate limiting. The report doesn't read NSE script output.

## If you use a different version

Flags and the XML format change from one version to the next. Run `make check` and a test run against a target of your own before trusting it. If you find a flag that bypasses the scope and isn't on the forbidden list, that's a vulnerability: see [SECURITY.md](../../SECURITY.md).
