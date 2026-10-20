import unittest
from unittest.mock import patch
import health_check


class HealthCheckTests(unittest.TestCase):
    def test_python_version_is_pass_on_current_runtime(self):
        result = health_check.check_python()
        self.assertIn(result["status"], ("PASS", "WARN"))
        self.assertEqual(result["name"], "Python version")

    @patch("health_check.shutil.which")
    def test_missing_required_command_fails(self, mock_which):
        mock_which.side_effect = lambda command: "/usr/bin/python3" if command == "python3" else None
        result = health_check.check_required_commands()
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("git", result["details"])

    @patch("health_check.shutil.disk_usage")
    @patch("health_check.Path.resolve")
    def test_low_disk_space_warns(self, mock_resolve, mock_usage):
        class Usage:
            total = 10 * 1024**3
            used = 9.5 * 1024**3
            free = 0.5 * 1024**3
        mock_usage.return_value = Usage()
        mock_resolve.return_value = "/fake"
        result = health_check.check_disk()
        self.assertEqual(result["status"], "WARN")


if __name__ == "__main__":
    unittest.main()
