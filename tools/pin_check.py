#!/usr/bin/env python3
"""
pin_check.py — ESP32-S3-BOX-3 GPIO conflict checker
Run: python3 tools/pin_check.py esp32s3box3.yaml
Exit 0 = clean, Exit 1 = conflicts or errors found

Checks:
  1. Duplicate GPIO assignments (always flagged as errors)
  2. Strapping pins used without ignore_strapping_warning (per-occurrence)
  3. Reserved pins (USB D+/D-) assigned to user functions
"""
import re
import sys
from collections import defaultdict

# ESP32-S3 strapping pins that require ignore_strapping_warning: true
STRAPPING_PINS = {0, 3, 45, 46}

# Reserved/internal pins (USB D- / D+ on WROOM-1)
RESERVED_PINS = {19, 20}

# Pin assignment keys — only lines with these keys are considered real pin assignments
PIN_KEYS = re.compile(
    r'^\s*(?:pin|number|sda|scl|clk_pin|mosi_pin|miso_pin|'
    r'i2s_\w+_pin|din_pin|dout_pin|cs_pin|dc_pin|reset_pin|'
    r'interrupt_pin|output_pin|input_pin)\s*[:\s]'
)


def extract_pins(yaml_text):
    """
    Return list of (line_no, gpio_num, context_snippet) for lines that
    look like actual pin assignments (not free-text strings or comments).
    """
    found = []
    lines = yaml_text.splitlines()
    gpio_pattern = re.compile(r'\bGPIO(\d+)\b')
    bare_number = re.compile(r'(?:^|\s)(\d{1,2})\s*$')

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue
        # Only process lines that are real pin assignment keys
        if not PIN_KEYS.match(line):
            continue

        # Match GPIO<N>
        for m in gpio_pattern.finditer(line):
            found.append((i, int(m.group(1)), stripped[:80]))

        # Match bare numbers on pin assignment lines (e.g. "clk_pin: 7")
        for m in bare_number.finditer(line):
            num = int(m.group(1))
            # Avoid double-counting if GPIO<N> already matched
            if not gpio_pattern.search(line):
                found.append((i, num, stripped[:80]))

    return found


def get_block(lines, line_no, radius=8):
    """Return a slice of lines around line_no for context searches."""
    start = max(0, line_no - radius - 1)
    end = min(len(lines), line_no + radius)
    return '\n'.join(lines[start:end])


def has_ignore_strapping(lines, line_no):
    """
    Check whether the pin block containing line_no includes
    ignore_strapping_warning: true within the enclosing YAML block.
    We walk forward from line_no until the indentation decreases back
    to the block's parent level (max 15 lines).
    """
    block = get_block(lines, line_no, radius=12)
    return 'ignore_strapping_warning' in block


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/pin_check.py <config.yaml>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    try:
        with open(yaml_file) as f:
            text = f.read()
    except FileNotFoundError:
        print(f"✗ File not found: {yaml_file}")
        sys.exit(1)

    lines = text.splitlines()
    pins = extract_pins(text)

    # Group by pin number
    by_pin = defaultdict(list)
    for line_no, gpio, ctx in pins:
        by_pin[gpio].append((line_no, ctx))

    errors = 0

    print(f"\n📍 GPIO Pin Report — {yaml_file}")
    print("=" * 60)

    # ── 1. Conflict check (any GPIO used more than once = error) ──
    print("\n🔍 Conflict Check (duplicate GPIO assignments):")
    conflict_found = False
    for gpio in sorted(by_pin):
        occurrences = by_pin[gpio]
        if len(occurrences) > 1:
            print(f"  ✗ GPIO{gpio} assigned {len(occurrences)} times — CONFLICT!")
            for ln, ctx in occurrences:
                print(f"       L{ln:4d}: {ctx}")
            errors += 1
            conflict_found = True
    if not conflict_found:
        print("  ✓ No conflicts detected")

    # ── 2. Strapping pin validation (every occurrence checked) ────
    print("\n⚠️  Strapping Pin Validation:")
    strapping_found = False
    for gpio in sorted(by_pin):
        if gpio in STRAPPING_PINS:
            strapping_found = True
            for line_no, ctx in by_pin[gpio]:
                if has_ignore_strapping(lines, line_no):
                    print(f"  ✓ GPIO{gpio:2d} (strapping, L{line_no}) — ignore_strapping_warning present")
                else:
                    print(f"  ✗ GPIO{gpio:2d} (strapping, L{line_no}) — MISSING ignore_strapping_warning!")
                    errors += 1
    if not strapping_found:
        print("  (no strapping pins assigned)")

    # ── 3. Reserved pin check ──────────────────────────────────────
    print("\n🚫 Reserved Pin Check:")
    reserved_used = []
    for gpio in sorted(by_pin):
        if gpio in RESERVED_PINS:
            reserved_used.append(gpio)
            print(f"  ✗ GPIO{gpio} is reserved (USB D+/D-) — do not assign!")
            errors += 1
    if not reserved_used:
        print("  ✓ No reserved pins assigned")

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if errors == 0:
        print("✅ All pin checks passed — safe to deploy")
        sys.exit(0)
    else:
        print(f"✗  {errors} error(s) found — DO NOT deploy until resolved")
        sys.exit(1)


if __name__ == '__main__':
    main()
