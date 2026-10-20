import socket
import unittest
from unittest.mock import patch

from connectivity_check import check_tcp_port


class ConnectivityCheckTests(unittest.TestCase):

    @patch("connectivity_check.socket.create_connection")
    def test_open_port(self, mock_connection):
        result = check_tcp_port("192.0.2.10", 443, timeout=0.5)

        self.assertEqual(result["status"], "OPEN")
        self.assertGreaterEqual(result["latency_ms"], 0)
        mock_connection.assert_called_once_with(
            ("192.0.2.10", 443),
            timeout=0.5,
        )

    @patch("connectivity_check.socket.create_connection")
    def test_connection_refused(self, mock_connection):
        mock_connection.side_effect = ConnectionRefusedError("refused")

        result = check_tcp_port("192.0.2.10", 443)

        self.assertEqual(result["status"], "CLOSED")
        self.assertEqual(result["detail"], "Connection refused")

    @patch("connectivity_check.socket.create_connection")
    def test_connection_timeout(self, mock_connection):
        mock_connection.side_effect = socket.timeout("timed out")

        result = check_tcp_port("192.0.2.10", 443)

        self.assertEqual(result["status"], "TIMEOUT")
        self.assertEqual(result["detail"], "Connection timed out")

    @patch("connectivity_check.socket.create_connection")
    def test_unreachable_network(self, mock_connection):
        mock_connection.side_effect = OSError("Network unreachable")

        result = check_tcp_port("192.0.2.10", 443)

        self.assertEqual(result["status"], "UNREACHABLE")
        self.assertIn("Network unreachable", result["detail"])


if __name__ == "__main__":
    unittest.main()
