"""Generate an HTML dashboard from a connectivity JSON report."""

import argparse
import html
import json
import sys
from pathlib import Path


def safe_text(value):
    """Escape values before inserting them into HTML."""
    return html.escape(str(value if value is not None else "—"))


def status_class(value):
    """Return a CSS class from a controlled set of names."""
    name = str(value or "INFO").lower()
    allowed = {
        "ok", "warning", "critical", "info", "not_run",
        "open", "closed", "timeout", "unreachable",
    }
    return name if name in allowed else "info"


def main():
    parser = argparse.ArgumentParser(
        description="Generate an HTML dashboard from a connectivity report."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("connectivity_report.json"),
        help="Input connectivity JSON report.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/connectivity_report.html"),
        help="Output HTML file.",
    )
    args = parser.parse_args()

    try:
        report = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Cannot read report: {exc}", file=sys.stderr)
        return 1

    if not isinstance(report, dict) or not isinstance(
        report.get("results"), list
    ):
        print("ERROR: Invalid report structure.", file=sys.stderr)
        return 1

    summary = report.get("summary", {})
    if not isinstance(summary, dict):
        print("ERROR: Invalid report summary.", file=sys.stderr)
        return 1

    rows = []
    for result in report["results"]:
        if not isinstance(result, dict):
            continue

        severity = result.get("severity", "INFO")
        latency = result.get("latency_ms")
        latency_text = "—" if latency is None else f"{latency} ms"

        rows.append(
            "<tr>"
            f"<td>{safe_text(result.get('device_id'))}</td>"
            f"<td>{safe_text(result.get('device_name'))}</td>"
            f"<td>{safe_text(result.get('ip_address'))}:"
            f"{safe_text(result.get('port'))}</td>"
            f"<td>{safe_text(result.get('service'))}</td>"
            f"<td><span class='badge {status_class(severity)}'>"
            f"{safe_text(severity)}</span></td>"
            f"<td>{safe_text(result.get('status'))}</td>"
            f"<td>{safe_text(latency_text)}</td>"
            f"<td>{safe_text(result.get('detail'))}</td>"
            "</tr>"
        )

    if not rows:
        rows.append("<tr><td colspan='8'>No results available.</td></tr>")

    mode = report.get("mode", "unknown")
    dry_run = mode == "dry-run"
    mode_note = (
        "DRY RUN — no network connections were attempted."
        if dry_run
        else "LIVE MODE — results reflect attempted TCP connections."
    )

    template = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IP Device Health Dashboard</title>
<style>
:root {
  color-scheme: light;
  --navy: #142238;
  --muted: #64748b;
  --line: #e2e8f0;
  --green: #166534;
  --green-bg: #dcfce7;
  --amber: #92400e;
  --amber-bg: #fef3c7;
  --red: #991b1b;
  --red-bg: #fee2e2;
  --blue: #334155;
  --blue-bg: #e2e8f0;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #f1f5f9;
  color: #1e293b;
  font-family: Arial, Helvetica, sans-serif;
}
header {
  background: var(--navy);
  color: white;
  padding: 28px 5%;
}
header h1 { margin: 0 0 8px; font-size: 28px; }
header p { margin: 5px 0; color: #cbd5e1; }
main { max-width: 1450px; margin: 28px auto; padding: 0 20px; }
.notice {
  padding: 14px 18px;
  border-radius: 10px;
  background: #e0f2fe;
  border-left: 5px solid #0284c7;
  margin-bottom: 22px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
  margin-bottom: 24px;
}
.card, .panel {
  background: white;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 18px;
}
.card h2 { font-size: 13px; color: var(--muted); margin: 0 0 10px; }
.metric { font-size: 30px; font-weight: 700; }
.panel { margin-bottom: 24px; }
.panel h2 { margin: 0 0 16px; font-size: 19px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
th { background: #f8fafc; color: #475569; }
.badge {
  display: inline-block;
  border-radius: 999px;
  padding: 5px 9px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;
}
.ok, .open { color: var(--green); background: var(--green-bg); }
.warning, .timeout { color: var(--amber); background: var(--amber-bg); }
.critical, .closed, .unreachable { color: var(--red); background: var(--red-bg); }
.info, .not_run { color: var(--blue); background: var(--blue-bg); }
footer { color: var(--muted); font-size: 12px; padding: 10px 0 28px; }
</style>
</head>
<body>
<header>
  <h1>IP Device Health Dashboard</h1>
  <p>Linux · Network diagnostics · Systems integration</p>
  <p>Generated at (UTC): __GENERATED__</p>
  <p>Overall status: <span class="badge __OVERALL_CLASS__">__OVERALL__</span></p>
</header>
<main>
  <div class="notice">__MODE_NOTE__</div>
  <section class="cards">
    <div class="card"><h2>Total checks</h2><div class="metric">__TOTAL__</div></div>
    <div class="card"><h2>OK</h2><div class="metric" style="color:#166534">__OK__</div></div>
    <div class="card"><h2>Warnings</h2><div class="metric" style="color:#b45309">__WARNING__</div></div>
    <div class="card"><h2>Critical</h2><div class="metric" style="color:#b91c1c">__CRITICAL__</div></div>
    <div class="card"><h2>Not run</h2><div class="metric">__NOT_RUN__</div></div>
  </section>
  <section class="panel">
    <h2>Device and port results</h2>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>ID</th><th>Device</th><th>Target</th><th>Service</th>
          <th>Severity</th><th>Status</th><th>Latency</th><th>Details</th>
        </tr></thead>
        <tbody>__ROWS__</tbody>
      </table>
    </div>
  </section>
  <footer>
    TCP connectivity alone does not confirm that an application, camera stream,
    or radar function is operating correctly.
  </footer>
</main>
</body>
</html>
"""

    replacements = {
        "__GENERATED__": safe_text(report.get("generated_at_utc")),
        "__OVERALL_CLASS__": status_class(report.get("overall_status")),
        "__OVERALL__": safe_text(report.get("overall_status", "UNKNOWN")),
        "__MODE_NOTE__": safe_text(mode_note),
        "__TOTAL__": safe_text(summary.get("total_checks", 0)),
        "__OK__": safe_text(summary.get("ok", 0)),
        "__WARNING__": safe_text(summary.get("warning", 0)),
        "__CRITICAL__": safe_text(summary.get("critical", 0)),
        "__NOT_RUN__": safe_text(summary.get("not_run", 0)),
        "__ROWS__": "\n".join(rows),
    }

    for key, value in replacements.items():
        template = template.replace(key, value)

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(template, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Cannot write HTML report: {exc}", file=sys.stderr)
        return 1

    print(f"HTML dashboard saved to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
