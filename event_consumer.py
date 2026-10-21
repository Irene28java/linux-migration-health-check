"""Consume and validate simulated device events from RabbitMQ."""

import json
import os
import sys
from pathlib import Path

import pika
from dotenv import load_dotenv


QUEUE_NAME = "device.health.events"

REQUIRED_FIELDS = (
    "event_id",
    "event_type",
    "device_id",
    "status",
    "timestamp_utc",
)


def on_message(channel, method, properties, body):
    """Validate one message and acknowledge it after processing."""
    try:
        event = json.loads(body.decode("utf-8"))

        if not isinstance(event, dict):
            raise ValueError("Event must be a JSON object")

        for field in REQUIRED_FIELDS:
            value = event.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Missing or invalid field: {field}")

    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Rejected invalid message: {exc}", file=sys.stderr)
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )
        return

    print("\nEVENT RECEIVED")
    print("=" * 40)
    print(f"Event ID:  {event['event_id']}")
    print(f"Device:    {event['device_id']}")
    print(f"Type:      {event['event_type']}")
    print(f"Status:    {event['status']}")
    print(f"Timestamp: {event['timestamp_utc']}")
    print(f"Message:   {event.get('message', '-')}")
    print(f"Simulated: {event.get('simulation', False)}")

    # Acknowledge only after successful validation and processing.
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main() -> int:
    """Connect to RabbitMQ and consume events."""
    load_dotenv(Path(__file__).resolve().parent / ".env")

    username = os.getenv("RABBITMQ_DEFAULT_USER")
    password = os.getenv("RABBITMQ_DEFAULT_PASS")

    if not username or not password:
        print("ERROR: RabbitMQ credentials are missing from .env.")
        return 1

    try:
        port = int(os.getenv("RABBITMQ_PORT", "5672"))
        credentials = pika.PlainCredentials(username, password)

        parameters = pika.ConnectionParameters(
            host="127.0.0.1",
            port=port,
            credentials=credentials,
            socket_timeout=5,
            connection_attempts=3,
            retry_delay=1,
        )

        connection = pika.BlockingConnection(parameters)

        try:
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=on_message,
                auto_ack=False,
            )

            print(f"Listening on queue: {QUEUE_NAME}")
            print("Press Ctrl+C to stop.")

            channel.start_consuming()

        except KeyboardInterrupt:
            print("\nConsumer stopped.")
        finally:
            if connection.is_open:
                connection.close()

        return 0

    except (pika.exceptions.AMQPError, OSError, ValueError) as exc:
        print(f"ERROR: Consumer failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
