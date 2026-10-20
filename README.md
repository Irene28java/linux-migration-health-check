# Linux Migration Health Check

Personal Linux administration and automation lab built with Python.

## Features

- Collects operating system and Python information.
- Checks available disk space.
- Checks for the DNS configuration file.
- Detects common system tools.
- Generates a JSON report.

## Requirements

- Linux or WSL2
- Python 3.10+

No third-party Python packages are required.

## Run

```bash
python3 health_check.py
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Limitations

This is a learning project, not a complete migration assessment.
DNS file presence does not guarantee DNS resolution.
Tool detection does not guarantee that services are healthy.

## Future improvements

- DNS resolution tests.
- Service health checks.
- Disk-space thresholds.
- GitHub Actions continuous integration.
- Migration validation and rollback procedures.
