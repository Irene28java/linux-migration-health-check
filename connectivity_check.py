"""TCP connectivity checks and JSON reporting for IP devices."""

import argparse
import json
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from device_inventory import load_inventory


def check_tcp_port(
    host: str,
    port: int,
    timeout: float = 1.0,
) -> dict:
    """Test a TCP port with a limited timeout."""
    started = time.perf_counter()

    try:
        with socket.create_connection(
            (host, port),
            timeout=timeout,
        ):
            status = "OPEN"
            detail = "TCP connection succeeded"

    except (socket.timeout, TimeoutError):
        status = "TIMEOUT"
        detail = "Connection timed out"

    except ConnectionRefusedError:
        status = "CLOSED"
        detail = "Connection refused"

    except OSError as exc:
        status = "UNREACHABLE"
        detail = str(exc) or "Network connection failed"

    latency_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    return {
        "status": status,
        "latency_ms": latency_ms,
        "detail": detail,
    }


def severity_for(status: str) -> str:
    """Map a connection result to an operational severity."""
    severities = {
        "OPEN": "OK",
        "CLOSED": "CRITICAL",
        "TIMEOUT": "WARNING",
        "UNREACHABLE": "CRITICAL",
        "NOT_RUN": "INFO",
    }
    return severities[status]


def build_report(
    devices: list[dict],
    live: bool,
    timeout: float,
) -> dict:
    """Build a report from the inventory and connectivity results."""
    results = []

    for device in devices:
        for port_config in device["ports_to_check"]:
            port = port_config["port"]

            if live:
                outcome = check_tcp_port(
                    device["ip_address"],
                    port,
                    timeout,
                )
            else:
                outcome = {
                    "status": "NOT_RUN",
                    "latency_ms": None,
                    "detail": "Dry run; no network connection attempted",
                }

            results.append({
                "device_id": device["id"],
                "device_name": device["name"],
                "device_type": device["type"],
                "ip_address": device["ip_address"],
                "port": port,
                "service": port_config["service"],
                "status": outcome["status"],
                "severity": severity_for(outcome["status"]),
                "latency_ms": outcome["latency_ms"],
                "detail": outcome["detail"],
            })

    summary = {
        "total_checks": len(results),
        "ok": sum(r["severity"] == "OK" for r in results),
        "warning": sum(
            r["severity"] == "WARNING" for r in results
        ),
        "critical": sum(
            r["severity"] == "CRITICAL" for r in results
        ),
        "not_run": sum(
            r["status"] == "NOT_RUN" for r in results
        ),
    }

    if not live:
        overall_status = "NOT_RUN"
    elif not results:
        overall_status = "NO_CHECKS"
    elif summary["critical"]:
        overall_status = "CRITICAL"
    elif summary["warning"]:
        overall_status = "WARNING"
    else:
        overall_status = "OK"

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if live else "dry-run",
        "overall_status": overall_status,
        "summary": summary,
        "results": results,
    }


def main() -> int:
    """Run connectivity checks and save the JSON report."""
    parser = argparse.ArgumentParser(
        description="Check configured TCP ports on authorized devices."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/devices.json"),
        help="Path to the device inventory.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Connection timeout in seconds (maximum 30).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("connectivity_report.json"),
        help="Path where the JSON report will be saved.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Make real TCP connections to authorized devices.",
    )
    args = parser.parse_args()

    if not 0 < args.timeout <= 30:
        parser.error("--timeout must be greater than 0 and at most 30")

    try:
        devices = load_inventory(args.config)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = build_report(devices, args.live, args.timeout)

    if not args.live:
        print("CONNECTIVITY REPORT - DRY RUN")
        print("No network connections were attempted.")
    else:
        print("TCP CONNECTIVITY REPORT")

    print("=" * 72)

    for result in report["results"]:
        if result["status"] == "NOT_RUN":
            print(
                f"[INFO] Planned: {result['device_id']} "
                f"{result['ip_address']}:{result['port']} "
                f"({result['service']})"
            )
        else:
            print(
                f"[{result['severity']}] {result['device_id']} "
                f"{result['ip_address']}:{result['port']} "
                f"({result['service']}) - "
                f"{result['status']} - "
                f"{result['latency_ms']} ms - "
                f"{result['detail']}"
            )

    summary = report["summary"]
    print("-" * 72)
    print(f"Overall status: {report['overall_status']}")
    print(
        f"Checks: {summary['total_checks']} | "
        f"OK: {summary['ok']} | "
        f"Warnings: {summary['warning']} | "
        f"Critical: {summary['critical']} | "
        f"Not run: {summary['not_run']}"
    )

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"ERROR: Cannot save report: {exc}", file=sys.stderr)
        return 2

    print(f"JSON report saved to: {args.output}")

    if not args.live:
        return 0
    if summary["critical"]:
        return 2
    if summary["warning"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
