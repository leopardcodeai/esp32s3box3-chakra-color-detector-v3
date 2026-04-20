#!/usr/bin/env python3
"""
hue_bridge_test.py - inspect and validate the ESP32 -> Hue pipeline.

Examples:
  python3 tools/hue_bridge_test.py inspect
  python3 tools/hue_bridge_test.py write-test --hue 25500 --sat 254 --bri 254
  python3 tools/hue_bridge_test.py write-test --strict-hue
  python3 tools/hue_bridge_test.py device-button --esp-host 192.168.178.108
  python3 tools/hue_bridge_test.py full --esp-host 192.168.178.108
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

try:
    from aioesphomeapi import APIClient, LogLevel
except ImportError:  # pragma: no cover - optional dependency for host-side device tests
    APIClient = None
    LogLevel = None


class TaggedLoader(yaml.SafeLoader):
    pass


def _unknown_tag(loader: TaggedLoader, tag_suffix: str, node: yaml.Node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


TaggedLoader.add_multi_constructor("", _unknown_tag)


def load_yaml(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=TaggedLoader)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["inspect", "write-test", "device-button", "full"])
    parser.add_argument("--device-config", default="device_config.yaml")
    parser.add_argument("--secrets", default="secrets.yaml")
    parser.add_argument("--hue", type=int, default=25500)
    parser.add_argument("--sat", type=int, default=254)
    parser.add_argument("--bri", type=int, default=254)
    parser.add_argument("--settle-seconds", type=float, default=1.5)
    parser.add_argument("--esp-host", default="esp32-s3box-3.local")
    parser.add_argument("--esp-port", type=int, default=6053)
    parser.add_argument("--button-name", default="Run Hue Pipeline Self-Test")
    parser.add_argument("--log-seconds", type=float, default=10.0)
    parser.add_argument("--strict-hue", action="store_true")
    parser.add_argument("--expect-colormode", default="hs")
    return parser.parse_args()


def request_json(method: str, url: str, payload: dict | None = None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
        return response.status, json.loads(body)


def get_state(base_url: str, light_id: str) -> dict:
    _, payload = request_json("GET", f"{base_url}/lights/{light_id}")
    return payload


def print_light_summary(light_id: str, payload: dict) -> None:
    state = payload.get("state", {})
    capabilities = payload.get("capabilities", {}).get("control", {})
    print(
        f"[LIGHT {light_id}] "
        f"name={payload.get('name')} "
        f"type={payload.get('type')} "
        f"reachable={state.get('reachable')} "
        f"on={state.get('on')} "
        f"colormode={state.get('colormode')} "
        f"has_gamut={'colorgamuttype' in capabilities}"
    )


def within_tolerance(actual: int | None, expected: int, tolerance: int) -> bool:
    if actual is None:
        return False
    return abs(actual - expected) <= tolerance


def load_runtime_config(args: argparse.Namespace) -> tuple[list[str], str, str, str]:
    device_config = load_yaml(Path(args.device_config))
    secrets = load_yaml(Path(args.secrets))

    substitutions = device_config.get("substitutions", {})
    light_control_mode = str(substitutions.get("light_control_mode", "")).strip()
    light_ids_raw = substitutions.get("hue_light_entity", "")
    if not light_ids_raw:
        raise RuntimeError("No hue_light_entity configured in device_config.yaml")
    if "${" in str(light_ids_raw):
        raise RuntimeError(f"hue_light_entity is unresolved: {light_ids_raw}")

    bridge_ip = secrets.get("hue_bridge_ip") or substitutions.get("hue_bridge_ip")
    api_key = secrets.get("hue_api_key") or substitutions.get("hue_api_key")
    if not bridge_ip or not api_key:
        raise RuntimeError("Missing hue_bridge_ip or hue_api_key")

    light_ids = [part.strip() for part in str(light_ids_raw).split(",") if part.strip()]
    return light_ids, str(bridge_ip), str(api_key), light_control_mode


def run_bridge_checks(args: argparse.Namespace, do_write: bool) -> int:
    light_ids, bridge_ip, api_key, light_control_mode = load_runtime_config(args)
    base_url = f"http://{bridge_ip}/api/{api_key}"
    failures = 0

    print(f"[INFO] Hue bridge: {bridge_ip}")
    print(f"[INFO] light_control_mode: {light_control_mode}")
    print(f"[INFO] Target lights: {', '.join(light_ids)}")
    if light_control_mode != "hue":
        print(f"[FAIL] Expected light_control_mode 'hue', got '{light_control_mode}'")
        failures += 1

    for light_id in light_ids:
        try:
            payload = get_state(base_url, light_id)
        except urllib.error.URLError as exc:
            print(f"[ERROR] Light {light_id}: request failed: {exc}")
            failures += 1
            continue

        print_light_summary(light_id, payload)
        state = payload.get("state", {})
        capabilities = payload.get("capabilities", {}).get("control", {})
        if not state.get("reachable", False):
            print(f"  [FAIL] Light {light_id} is not reachable")
            failures += 1
        if "colorgamuttype" not in capabilities:
            print(f"  [FAIL] Light {light_id} does not expose color gamut control")
            failures += 1

    if do_write:
        payload = {"on": True, "bri": args.bri, "hue": args.hue, "sat": args.sat}
        print(f"[INFO] Writing test payload: {payload}")
        for light_id in light_ids:
            try:
                status, response = request_json("PUT", f"{base_url}/lights/{light_id}/state", payload)
            except urllib.error.URLError as exc:
                print(f"[ERROR] Light {light_id}: write failed: {exc}")
                failures += 1
                continue
            print(f"[WRITE {light_id}] status={status} response={response}")
            if status != 200:
                print(f"  [FAIL] Light {light_id}: unexpected HTTP status {status}")
                failures += 1

        time.sleep(args.settle_seconds)

        for light_id in light_ids:
            try:
                payload_after = get_state(base_url, light_id)
            except urllib.error.URLError as exc:
                print(f"[ERROR] Light {light_id}: post-write read failed: {exc}")
                failures += 1
                continue

            state = payload_after.get("state", {})
            actual_hue = state.get("hue")
            actual_sat = state.get("sat")
            actual_bri = state.get("bri")
            actual_colormode = state.get("colormode")
            print(
                f"[VERIFY {light_id}] "
                f"on={state.get('on')} bri={actual_bri} "
                f"hue={actual_hue} sat={actual_sat} "
                f"colormode={actual_colormode} xy={state.get('xy')}"
            )
            if state.get("on") is not True:
                print(f"  [FAIL] Light {light_id} is not on after write-test")
                failures += 1
            if actual_colormode != args.expect_colormode:
                print(
                    f"  [FAIL] Light {light_id}: colormode {actual_colormode!r} "
                    f"!= expected {args.expect_colormode!r}"
                )
                failures += 1
            if not within_tolerance(actual_hue, args.hue, 256):
                message = (
                    f"  [WARN] Light {light_id}: hue {actual_hue} != requested {args.hue} "
                    "(Hue lamps may remap hue values to their reachable gamut)"
                )
                if args.strict_hue:
                    print(message.replace("[WARN]", "[FAIL]"))
                    failures += 1
                else:
                    print(message)
            if not within_tolerance(actual_sat, args.sat, 5):
                print(f"  [FAIL] Light {light_id}: sat {actual_sat} != expected {args.sat}")
                failures += 1
            if not within_tolerance(actual_bri, args.bri, 5):
                print(f"  [FAIL] Light {light_id}: bri {actual_bri} != expected {args.bri}")
                failures += 1

    return failures


async def run_device_button_test(args: argparse.Namespace) -> int:
    if APIClient is None or LogLevel is None:
        print("[ERROR] aioesphomeapi is not available; cannot run device-button test")
        return 1

    client = APIClient(args.esp_host, args.esp_port, None)
    await client.connect(login=False)
    entities, _services = await client.list_entities_services()

    button_map = {
        getattr(entity, "name", ""): getattr(entity, "key", 0)
        for entity in entities
        if entity.__class__.__name__.endswith("ButtonInfo")
    }
    if args.button_name not in button_map:
        print(f"[ERROR] Button not found: {args.button_name}")
        print("[INFO] Available buttons:")
        for name in sorted(button_map):
            print(f"  - {name}")
        await client.disconnect()
        return 1

    log_tags = (
        "test_hue",
        "hue_inspect",
        "hue_test",
        "hue_send",
        "hue_response",
        "hue_error",
        "hue_sync",
        "pipeline_test",
        "chakra_send",
        "chakra_hue",
    )

    def on_log(msg) -> None:
        text = getattr(msg, "message", b"")
        if isinstance(text, bytes):
            text = text.decode(errors="replace")
        if any(tag in text for tag in log_tags):
            print(text, end="")

    unsub = client.subscribe_logs(on_log, log_level=LogLevel.LOG_LEVEL_DEBUG, dump_config=False)
    await asyncio.sleep(1)
    print(f"[INFO] Pressing device button: {args.button_name}")
    client.button_command(button_map[args.button_name])
    await asyncio.sleep(args.log_seconds)
    unsub()
    await client.disconnect()
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "inspect":
            failures = run_bridge_checks(args, do_write=False)
        elif args.command == "write-test":
            failures = run_bridge_checks(args, do_write=True)
        elif args.command == "device-button":
            return asyncio.run(run_device_button_test(args))
        else:
            failures = run_bridge_checks(args, do_write=True)
            button_rc = asyncio.run(run_device_button_test(args))
            if button_rc != 0:
                failures += 1
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 1

    if failures:
        print(f"[RESULT] FAIL ({failures} issue(s))")
        return 1

    print("[RESULT] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
