#!/usr/bin/env python3
"""
Chakra Listener — subscribes to relay SSE and controls a local HA light.

Deploy on any VM running Home Assistant:
    pip install requests sseclient-py
    python3 chakra_listener.py --ha-token YOUR_TOKEN

Subscribes to the Audio FFT Relay's /aws/audio/live SSE stream.
Each event contains a chakra detection with RGB color.
This script calls the local HA REST API to set the light.

# ── systemd unit ──────────────────────────────────────────────────
# /etc/systemd/system/chakra-listener.service
# [Unit]
# Description=Chakra SSE Listener → HA Light
# After=network-online.target home-assistant.service
# Wants=network-online.target
#
# [Service]
# Type=simple
# User=homeassistant
# Environment=HA_TOKEN=<your_long_lived_token>
# Environment=RELAY_URL=http://<relay-ip>:8765
# Environment=LIGHT_ENTITY=light.living_room
# ExecStart=/usr/bin/python3 /opt/chakra/chakra_listener.py
# Restart=always
# RestartSec=10
#
# [Install]
# WantedBy=multi-user.target
"""

import argparse
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime

import requests
import sseclient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("chakra")

# ═══════════════════════════════════════════════════════════════════
#  Globals
# ═══════════════════════════════════════════════════════════════════
running = True
last_ha_call = 0.0
last_chakra = -1
HA_RATE_LIMIT = 2.0  # seconds between HA API calls


def signal_handler(sig, frame):
    global running
    log.info("Shutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def set_ha_light(ha_url: str, token: str, entity: str, r: int, g: int, b: int):
    """Call HA REST API to set light color."""
    global last_ha_call, last_chakra
    url = f"{ha_url}/api/services/light/turn_on"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "entity_id": entity,
        "rgb_color": [r, g, b],
        "brightness": 255,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=5)
        if resp.status_code == 200:
            log.info(f"Light → RGB({r},{g},{b})")
        else:
            log.warning(f"HA returned {resp.status_code}: {resp.text[:100]}")
    except requests.RequestException as e:
        log.error(f"HA call failed: {e}")


def listen(relay_url: str, ha_url: str, token: str, entity: str):
    """Connect to SSE stream and process chakra events."""
    global last_ha_call, last_chakra

    sse_url = f"{relay_url}/aws/audio/live"
    log.info(f"Connecting to {sse_url}")

    resp = requests.get(sse_url, stream=True, timeout=30)
    resp.raise_for_status()
    client = sseclient.SSEClient(resp)

    for event in client.events():
        if not running:
            break

        try:
            data = json.loads(event.data)
        except (json.JSONDecodeError, TypeError):
            continue

        chakra_idx = data.get("chakra_index", -1)
        chakra_name = data.get("chakra_name", "?")
        freq = data.get("frequency", 0)
        r, g, b = data.get("r", 0), data.get("g", 0), data.get("b", 0)

        log.info(f"← {chakra_name} @ {freq} Hz")

        # Rate-limit + deduplicate
        now = time.time()
        if chakra_idx == last_chakra and (now - last_ha_call) < HA_RATE_LIMIT:
            continue

        last_chakra = chakra_idx
        last_ha_call = now
        set_ha_light(ha_url, token, entity, r, g, b)


def main():
    parser = argparse.ArgumentParser(description="Chakra SSE Listener → HA Light")
    parser.add_argument(
        "--relay-url",
        default=os.environ.get("RELAY_URL", "http://localhost:8765"),
        help="Audio FFT Relay URL (default: $RELAY_URL or http://localhost:8765)",
    )
    parser.add_argument(
        "--ha-url",
        default=os.environ.get("HA_URL", "http://localhost:8123"),
        help="Home Assistant URL (default: $HA_URL or http://localhost:8123)",
    )
    parser.add_argument(
        "--ha-token",
        default=os.environ.get("HA_TOKEN"),
        help="HA long-lived access token (or set $HA_TOKEN)",
    )
    parser.add_argument(
        "--light",
        default=os.environ.get("LIGHT_ENTITY", "light.living_room"),
        help="HA light entity_id (default: $LIGHT_ENTITY or light.living_room)",
    )
    args = parser.parse_args()

    if not args.ha_token:
        log.error("HA_TOKEN required. Use --ha-token or set $HA_TOKEN")
        sys.exit(1)

    log.info(f"Relay:  {args.relay_url}")
    log.info(f"HA:     {args.ha_url}")
    log.info(f"Light:  {args.light}")

    while running:
        try:
            listen(args.relay_url, args.ha_url, args.ha_token, args.light)
        except (requests.RequestException, ConnectionError) as e:
            log.warning(f"Connection lost: {e}")
        except Exception as e:
            log.error(f"Unexpected error: {e}")

        if running:
            log.info("Reconnecting in 5s...")
            time.sleep(5)

    log.info("Goodbye.")


if __name__ == "__main__":
    main()
