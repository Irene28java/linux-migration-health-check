"""Create a clearly simulated connectivity report for the portfolio."""

import json
from datetime import datetime, timezone
from pathlib import Path


SOURCE = Path("connectivity_report.json")
DESTINATION = Path("examples/demo_connectivity_report.json")

DEMO_RESULTS = [
    ("OPEN", "OK", 14.2, "Demo: TCP connection succeeded"),
    ("TIMEOUT", "WARNING", 1000.0, "Demo: connection timed out"),
    ("CLOSED", "CRITICAL", 6.5, "Demo: connection refused"),
    ("OPEN", "OK", 19.8, "Demo: TCP connection succeeded"),
    ("CLOSED", "CRITICAL", 3.1, "Demo: connection refused"),
    ("OPEN", "OK", 15.4, "Demo: TCP connection succeeded"),
]


def main():
    report = json.loads(SOURCE.read_text(encoding="utf-8"))

    if len(report.get("results", [])) != len(DEMO_RESULTS):
        raise ValueError(
            "Expected six configured checks in the source report."
        )

    for result, demo in zip(report["results"], DEMO_RESULTS):
        status, severity, latency, detail = demo
        result["status"] = status
        result["severity"] = severity
        result["latency_ms"] = latency
        result["detail"] = detail

    report["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["mode"] = "demo"
    report["overall_status"] = "CRITICAL"
    report["summary"] = {
        "total_checks": 6,
        "ok": 3,
        "warning": 1,
        "critical": 2,
        "not_run": 0,
    }

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Demo report created: {DESTINATION}")
    print("SIMULATED DATA ONLY — no network checks were performed.")


if __name__ == "__main__":
    main()
	

