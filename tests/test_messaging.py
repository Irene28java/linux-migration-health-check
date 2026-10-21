import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from event_consumer import on_message


class FakeChannel:
    def __init__(self):
        self.acknowledged = []
        self.rejected = []

    def basic_ack(self, delivery_tag):
        self.acknowledged.append(delivery_tag)

    def basic_nack(self, delivery_tag, requeue):
        self.rejected.append((delivery_tag, requeue))


class MessagingTests(unittest.TestCase):

    def setUp(self):
        self.channel = FakeChannel()
        self.method = SimpleNamespace(delivery_tag=42)

    def valid_event(self):
        return {
            "event_id": "test-event-001",
            "event_type": "device.health",
            "device_id": "CAM-001",
            "status": "WARNING",
            "timestamp_utc": "2026-10-21T08:00:00+00:00",
            "simulation": True,
        }

    @patch("builtins.print")
    def test_valid_event_is_acknowledged(self, mock_print):
        body = json.dumps(self.valid_event()).encode("utf-8")

        on_message(self.channel, self.method, None, body)

        self.assertEqual(self.channel.acknowledged, [42])
        self.assertEqual(self.channel.rejected, [])

    @patch("builtins.print")
    def test_invalid_json_is_rejected(self, mock_print):
        on_message(
            self.channel,
            self.method,
            None,
            b"{invalid-json",
        )

        self.assertEqual(self.channel.acknowledged, [])
        self.assertEqual(self.channel.rejected, [(42, False)])

    @patch("builtins.print")
    def test_missing_required_field_is_rejected(self, mock_print):
        event = self.valid_event()
        del event["timestamp_utc"]

        on_message(
            self.channel,
            self.method,
            None,
            json.dumps(event).encode("utf-8"),
        )

        self.assertEqual(self.channel.acknowledged, [])
        self.assertEqual(self.channel.rejected, [(42, False)])


if __name__ == "__main__":
    unittest.main()
