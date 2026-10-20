# Linux Migration Health Check

A small, read-only Python utility that performs baseline checks before moving an application to a Linux host. It prints a human-readable summary and creates a JSON report.

> **Scope:** this is a learning portfolio project, not a production migration tool. It does not change system configuration, install packages, restart services, or contact external hosts.

## What it checks

- Operating system identification (`/etc/os-release` when available)
- Python version (3.10+ recommended)
- Available disk space (1 GiB advisory threshold)
- Presence of `python3` and `git`
- DNS resolver configuration file
- Whether `systemctl` is available

The checks are intentionally simple and advisory. A passing report does not prove that an application is compatible or that a migration is safe.

## Requirements

- Python 3.10+
- Linux, macOS, or another Python-capable environment (some checks are Linux-specific)
- Git for the required-command check

## Run it

```bash
python3 health_check.py
```

The command prints a summary and writes `report.json` in the current directory. The report is ignored by Git because it can contain host-specific information. The script returns a non-zero exit code if a check reports `FAIL`, so it can be used by other automation.

## Run tests locally

```bash
python3 -m unittest discover -s tests -v
```

## Continuous integration

GitHub Actions runs the unit tests automatically on every push and pull request. Check the **Actions** tab in the GitHub repository to see whether the workflow passed.

## Example use case

Before migrating a small Python service to a Linux VM, run the checks and review the output. Investigate warnings and failures, verify application dependencies separately, then test the service in a staging environment before production cutover.

## Limitations

- DNS checking only verifies that `/etc/resolv.conf` exists; it does not perform a DNS lookup.
- The disk threshold is advisory and does not account for the application's actual storage needs.
- The report does not prove service health or migration readiness.

## Skills demonstrated

Python standard library, safe subprocess use, filesystem inspection, JSON reporting, unit testing, Git, technical documentation, and CI with GitHub Actions.
