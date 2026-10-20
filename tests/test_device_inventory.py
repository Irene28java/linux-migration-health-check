import json
import tempfile
import unittest
from pathlib import Path

from device_inventory import load_inventory


class DeviceInventoryTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.config_path = Path(self.temp_dir.name) / "devices.json"

        self.device = {
            "id": "CAM-001",
            "name": "Test camera",
            "type": "camera",
            "ip_address": "192.0.2.10",
            "manufacturer": "Test manufacturer",
            "model": "TEST-01",
            "location": "Test lab",
        }

    def write_config(self, devices, schema_version=1):
        data = {
            "schema_version": schema_version,
            "devices": devices,
        }
        self.config_path.write_text(
            json.dumps(data),
            encoding="utf-8",
        )
        return self.config_path

    def test_loads_valid_inventory(self):
        path = self.write_config([self.device])

        devices = load_inventory(path)

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["id"], "CAM-001")

    def test_rejects_invalid_ip(self):
        device = self.device.copy()
        device["ip_address"] = "300.300.1.1"
        path = self.write_config([device])

        with self.assertRaisesRegex(ValueError, "invalid IP address"):
            load_inventory(path)

    def test_rejects_duplicate_ids(self):
        second = self.device.copy()
        second["ip_address"] = "192.0.2.11"
        path = self.write_config([self.device, second])

        with self.assertRaisesRegex(ValueError, "Duplicate device ID"):
            load_inventory(path)

    def test_rejects_duplicate_ips(self):
        second = self.device.copy()
        second["id"] = "CAM-002"
        path = self.write_config([self.device, second])

        with self.assertRaisesRegex(ValueError, "Duplicate IP address"):
            load_inventory(path)

    def test_rejects_unsupported_device_type(self):
        device = self.device.copy()
        device["type"] = "unknown"
        path = self.write_config([device])

        with self.assertRaisesRegex(ValueError, "unsupported type"):
            load_inventory(path)

    def test_rejects_missing_required_field(self):
        device = self.device.copy()
        del device["manufacturer"]
        path = self.write_config([device])

        with self.assertRaisesRegex(ValueError, "manufacturer"):
            load_inventory(path)

    def test_rejects_unsupported_schema_version(self):
        path = self.write_config(
            [self.device],
            schema_version=99,
        )

        with self.assertRaisesRegex(ValueError, "schema_version"):
            load_inventory(path)

    def test_loads_configured_ports(self):
        device = self.device.copy()
        device["ports_to_check"] = [
            {"port": 443, "service": "HTTPS"}
        ]
        path = self.write_config([device])

        devices = load_inventory(path)

        self.assertEqual(
            devices[0]["ports_to_check"],
            [{"port": 443, "service": "HTTPS"}],
        )

    def test_rejects_invalid_port(self):
        device = self.device.copy()
        device["ports_to_check"] = [
            {"port": 70000, "service": "HTTP"}
        ]
        path = self.write_config([device])

        with self.assertRaisesRegex(ValueError, "invalid port"):
            load_inventory(path)

    def test_rejects_duplicate_ports(self):
        device = self.device.copy()
        device["ports_to_check"] = [
            {"port": 443, "service": "HTTPS"},
            {"port": 443, "service": "HTTPS"},
        ]
        path = self.write_config([device])

        with self.assertRaisesRegex(ValueError, "duplicate port"):
            load_inventory(path)
if __name__ == "__main__":
    unittest.main()
