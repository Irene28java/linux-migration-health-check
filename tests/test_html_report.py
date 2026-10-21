import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "html_report.py"


class HTMLReportTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.folder = Path(self.temp_dir.name)
        self.source = self.folder / "report.json"
        self.output = self.folder / "dashboard.html"

    def run_report(self):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--input", str(self.source),
                "--output", str(self.output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def valid_report(self):
        return {
            "generated_at_utc": "2026-10-21T05:00:00+00:00",
            "mode": "demo",
            "overall_status": "WARNING",
            "summary": {
                "total_checks": 1,
                "ok": 0,
                "warning": 1,
                "critical": 0,
                "not_run": 0,
            },
            "results": [
                {
                    "device_id": "CAM-001",
                    "device_name": "Demo camera",
                    "ip_address": "192.0.2.10",
                    "port": 443,
                    "service": "HTTPS",
                    "severity": "WARNING",
                    "status": "TIMEOUT",
                    "latency_ms": 1000.0,
                    "detail": "Demo timeout",
                }
            ],
        }

    def test_generates_dashboard_with_demo_warning(self):
        self.source.write_text(
            json.dumps(self.valid_report()),
            encoding="utf-8",
        )

        result = self.run_report()

        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.output.read_text(encoding="utf-8")
        self.assertIn("DEMO DATA", page)
        self.assertIn("badge warning", page)
        self.assertIn("CAM-001", page)
        self.assertIn("TIMEOUT", page)

    def test_escapes_html_in_device_name(self):
        report = self.valid_report()
        report["results"][0]["device_name"] = (
            "<script>alert('test')</script>"
        )
        self.source.write_text(
            json.dumps(report),
            encoding="utf-8",
        )

        result = self.run_report()

        self.assertEqual(result.returncode, 0, result.stderr)
        page = self.output.read_text(encoding="utf-8")
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>alert('test')</script>", page)

    def test_rejects_invalid_json(self):
        self.source.write_text("{ invalid json", encoding="utf-8")

        result = self.run_report()

        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot read report", result.stderr)


if __name__ == "__main__":
    unittest.main()
