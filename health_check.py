#!/usr/bin/env python3
"""Read-only Linux migration readiness checks. No system changes are made."""
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def command_output(command):
    """Return command output safely; never raise if a tool is unavailable."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=3, check=False
        )
        return result.stdout.strip() or result.stderr.strip() or f"exit={result.returncode}"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return f"unavailable: {exc.__class__.__name__}"


def check_python():
    return {
        "name": "Python version",
        "status": "PASS" if sys.version_info >= (3, 10) else "WARN",
        "details": platform.python_version(),
    }


def check_disk(path="."):
    usage = shutil.disk_usage(path)
    free_gb = usage.free / (1024 ** 3)
    return {
        "name": "Disk space",
        "status": "PASS" if free_gb >= 1 else "WARN",
        "details": f"{free_gb:.2f} GiB free at {Path(path).resolve()} (1 GiB recommended)",
    }


def check_required_commands():
    required = ("python3", "git")
    missing = [cmd for cmd in required if shutil.which(cmd) is None]
    return {
        "name": "Required commands",
        "status": "PASS" if not missing else "FAIL",
        "details": "Found: python3, git" if not missing else "Missing: " + ", ".join(missing),
    }


def check_os():
    os_release = Path("/etc/os-release")
    if os_release.exists():
        lines = os_release.read_text(encoding="utf-8", errors="replace").splitlines()
        pretty_name = next((line.split("=", 1)[1].strip('"')
                            for line in lines if line.startswith("PRETTY_NAME=")), "Unknown Linux")
    else:
        pretty_name = platform.platform()
    return {"name": "Operating system", "status": "INFO", "details": pretty_name}


def check_network_dns():
    # Read-only diagnostic; does not send traffic to external hosts.
    resolver = Path("/etc/resolv.conf")
    exists = resolver.exists()
    return {
        "name": "DNS resolver configuration",
        "status": "PASS" if exists else "WARN",
        "details": str(resolver) + (" exists" if exists else " not found"),
    }


def check_service_manager():
    systemctl = shutil.which("systemctl")
    if not systemctl:
        return {"name": "systemd availability", "status": "INFO",
                "details": "systemctl not found; this environment may not use systemd"}
    return {"name": "systemd availability", "status": "INFO",
            "details": command_output([systemctl, "--version"]).splitlines()[0]}


def run_checks():
    return [
        check_os(),
        check_python(),
        check_disk(),
        check_required_commands(),
        check_network_dns(),
        check_service_manager(),
    ]


def main():
    results = run_checks()
    failed = sum(result["status"] == "FAIL" for result in results)
    warnings = sum(result["status"] == "WARN" for result in results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "checks": results,
        "summary": {"total": len(results), "failed": failed, "warnings": warnings},
        "note": "Read-only checks; results are advisory and do not guarantee migration readiness.",
    }

    print("LINUX MIGRATION HEALTH CHECK")
    print("=" * 32)
    for result in results:
        print(f'[{result["status"]}] {result["name"]}: {result["details"]}')
    print("-" * 32)
    print(f'Checks: {len(results)} | Failed: {failed} | Warnings: {warnings}')

    output = Path("report.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"JSON report saved to: {output.resolve()}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
