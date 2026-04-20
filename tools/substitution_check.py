#!/usr/bin/env python3
"""
substitution_check.py - detect self-referential ESPHome substitutions.

Example:
  python3 tools/substitution_check.py esp32s3box3_v4.yaml device_config.yaml
"""

from __future__ import annotations

import pathlib
import re
import sys


SELF_REF_RE = re.compile(
    r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_]+)\s*:\s*[\"']?\$\{(?P=key)\}[\"']?\s*(?:#.*)?$"
)


def check_file(path: pathlib.Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    in_substitutions = False
    substitutions_indent = None

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("substitutions:"):
            in_substitutions = True
            substitutions_indent = len(line) - len(line.lstrip(" "))
            continue

        if in_substitutions:
            current_indent = len(line) - len(line.lstrip(" "))
            if stripped and not stripped.startswith("#") and current_indent <= substitutions_indent:
                in_substitutions = False
                substitutions_indent = None

        if not in_substitutions:
            continue

        match = SELF_REF_RE.match(line)
        if match:
            findings.append((line_no, match.group("key"), line.rstrip()))
    return findings


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 tools/substitution_check.py <yaml-file> [<yaml-file> ...]")
        return 1

    has_errors = False
    for raw_path in sys.argv[1:]:
        path = pathlib.Path(raw_path)
        if not path.exists():
            print(f"[ERROR] File not found: {path}")
            has_errors = True
            continue

        findings = check_file(path)
        if findings:
            has_errors = True
            print(f"[ERROR] Self-referential substitutions found in {path}:")
            for line_no, key, line in findings:
                print(f"  L{line_no}: key '{key}' references itself -> {line}")
        else:
            print(f"[OK] {path}: no self-referential substitutions found")

    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
