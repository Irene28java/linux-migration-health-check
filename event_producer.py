"""Publish a simulated device event to RabbitMQ."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pika
from dotenv import load_dotenv


QUEUE_NAME = "device.health.events"


def main() -> int:
    """Connect to RabbitMQ and publish one demo event."""
    load_dotenv(Path(__file__).resolve().parent / ".env")

    username = os.getenv("RABBITMQ_DEFAULT_USER")
    password = os.getenv("RABBITMQ_DEFAULT_PASS")

    if not username or not password:
        print("ERROR: RabbitMQ credentials are missing from .env.")
        return 1

    try:
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        timeout = float(os.getenv("RABBITMQ_TIMEOUT", "5"))

        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(
            host="127.0.0.1",
            port=port,
            credentials=credentials,
            socket_timeout=timeout,
            connection_attempts=3,
            retry_delay=1,
        )

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": "device.health",
            "device_id": "CAM-001",
            "device_type": "camera",
            "status": "WARNING",
            "severity": "WARNING",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "message": "Simulated camera connectivity warning",
            "simulation": True,
        }

        connection = pika.BlockingConnection(parameters)
        try:
            channel = connection.channel()
            channel.queue_declare(
                queue=QUEUE_NAME,
                durable=True,
            )

            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=json.dumps(event, ensure_ascii=False),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    message_id=event["event_id"],
                ),
                mandatory=True,
            )

            print(f"Event published to queue: {QUEUE_NAME}")
            print(json.dumps(event, indent=2, ensure_ascii=False))
        finally:
            connection.close()

        return 0

    except (pika.exceptions.AMQPError, OSError, ValueError) as exc:
        print(f"ERROR: Could not publish event: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
