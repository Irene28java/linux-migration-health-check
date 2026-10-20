"""Device inventory tool for Linux infrastructure."""

import argparse
import ipaddress
import json
import sys
from pathlib import Path


REQUIRED_FIELDS = (
    "id",
    "name",
    "type",
    "ip_address",
    "manufacturer",
    "model",
    "location",
)

VALID_TYPES = {"camera", "radar", "communications"}


def load_inventory(config_path: Path) -> list[dict[str, str]]:
    """Load the inventory and validate its contents."""
    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"Cannot read configuration file: {exc}"
        ) from exc

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON at line {exc.lineno}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("The configuration must be a JSON object.")

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported or missing schema_version.")

    devices = data.get("devices")
    if not isinstance(devices, list) or not devices:
        raise ValueError("'devices' must be a non-empty list.")

    validated_devices: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_ips: set[str] = set()

    for number, device in enumerate(devices, start=1):
        if not isinstance(device, dict):
            raise ValueError(f"Device #{number} must be an object.")

        for field in REQUIRED_FIELDS:
            value = device.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Device #{number}: '{field}' is required."
                )

        device_id = device["id"].strip()
        device_type = device["type"].strip().lower()
        ip_address = device["ip_address"].strip()

        if device_type not in VALID_TYPES:
            raise ValueError(
                f"Device '{device_id}': unsupported type "
                f"'{device_type}'."
            )

        try:
            normalized_ip = str(ipaddress.ip_address(ip_address))
        except ValueError as exc:
            raise ValueError(
                f"Device '{device_id}': invalid IP address "
                f"'{ip_address}'."
            ) from exc

        if device_id in seen_ids:
            raise ValueError(f"Duplicate device ID: '{device_id}'.")

        if normalized_ip in seen_ips:
            raise ValueError(f"Duplicate IP address: '{ip_address}'.")

        seen_ids.add(device_id)
        seen_ips.add(normalized_ip)

        validated_device = {
            field: device[field].strip()
            for field in REQUIRED_FIELDS
        }

        if "description" in device:
            description = device["description"]
            if not isinstance(description, str):
                raise ValueError(
                    f"Device '{device_id}': description must be text."
                )
            validated_device["description"] = description.strip()

        validated_device["type"] = device_type
        validated_device["ip_address"] = normalized_ip

        validated_devices.append(validated_device)

    return validated_devices


def display_inventory(devices: list[dict[str, str]]) -> None:
    """Display the inventory in a readable terminal table."""
    print("\nDEVICE INVENTORY")
    print("=" * 105)
    print(
        f"{'ID':<10} {'TYPE':<16} {'IP ADDRESS':<18} "
        f"{'LOCATION':<22} NAME"
    )
    print("-" * 105)

    for device in devices:
        print(
            f"{device['id']:<10} "
            f"{device['type']:<16} "
            f"{device['ip_address']:<18} "
            f"{device['location']:<22} "
            f"{device['name']}"
        )

    print("-" * 105)
    print(f"Total devices: {len(devices)}")


def main() -> int:
    """Run the inventory command."""
    parser = argparse.ArgumentParser(
        description="Validate and display an IP device inventory."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/devices.json"),
        help="Path to the inventory JSON file.",
    )
    args = parser.parse_args()

    try:
        devices = load_inventory(args.config)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    display_inventory(devices)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())	

