import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "health_check.py"


class HealthCheckTests(unittest.TestCase):

    def test_generates_valid_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=15,
            )

            self.assertEqual(result.returncode, 0, result.stderr)

            report_path = Path(tmp) / "report.json"
            self.assertTrue(report_path.exists())

            report = json.loads(
                report_path.read_text(encoding="utf-8")
            )
            self.assertEqual(
                report["project"], "Linux Migration Health Check"
            )
            self.assertIn("checks", report)
            self.assertIn("python_version", report["checks"])

    def test_detects_system_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(SCRIPT)],
                cwd=tmp,
                check=True,
                capture_output=True,
                text=True,
                timeout=15,
            )

            report = json.loads(
                (Path(tmp) / "report.json").read_text(
                    encoding="utf-8"
                )
            )
            tools = report["checks"]["tools"]
            self.assertIn("python3", tools)
            self.assertIn("git", tools)
            self.assertTrue(
                all(isinstance(value, bool) for value in tools.values())
            )


if __name__ == "__main__":
    unittest.main()
