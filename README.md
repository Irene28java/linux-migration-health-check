# Linux Migration & IP Device Health Check

A Python toolkit for Linux pre-migration checks, IP device inventory,
and TCP connectivity diagnostics.

This project demonstrates practical skills in Python, Linux, IP networking,
configuration validation, automated testing, and continuous integration.

## Features

### Linux health checks
- Operating system and kernel information
- Python version validation
- Available disk space
- Required command availability
- DNS resolver configuration check
- systemd availability

### IP device inventory
- JSON-based device configuration
- Camera, radar, and communications device types
- IP address validation
- Duplicate ID and IP detection
- TCP port configuration validation

### TCP connectivity diagnostics
- Configured TCP port checks
- Connection timeout handling
- Response-time measurement
- JSON reports with UTC timestamps
- Dry-run mode enabled by default

## Requirements

- Python 3.10 or newer.
RabbitMQ dependencies are listed in requirements.txt (Pika and python-dotenv).

## Getting started

Run the Linux health checks:

    python3 health_check.py

Display the device inventory:

    python3 device_inventory.py

Preview connectivity checks without network connections:

    python3 connectivity_check.py

Run all automated tests:

    python3 -m unittest discover -s tests -v

## Safety and limitations

The inventory uses demonstration devices and documentation IP addresses.
The dry-run mode does not attempt network connections.
Live checks should only target authorized devices and networks.
An open TCP port does not prove that a camera stream or radar function works.

## Automated testing

Unit tests cover inventory validation and simulated TCP connection outcomes.
GitHub Actions runs the tests on pushes and pull requests.

## Future improvements

- Application-level checks for supported camera and radar protocols.
- Additional application-level checks.
- Expanded technical documentation.

## RabbitMQ event messaging

The project includes a local RabbitMQ messaging demo using Docker,
Python, Pika, and JSON events.

### Start RabbitMQ

Create a local `.env` file with your own development credentials.
Use `.env.example` as a template. Do not commit `.env`.

Start the service:

    docker compose up -d

Install Python dependencies in a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt

Publish a simulated device event:

    python event_producer.py

Consume events from another terminal:

    python event_consumer.py

RabbitMQ management UI: http://localhost:15672

The events are simulated. No real cameras or radar devices are contacted.
