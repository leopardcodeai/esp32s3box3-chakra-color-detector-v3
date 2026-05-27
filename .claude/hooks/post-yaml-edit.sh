#!/usr/bin/env bash
# Post-edit hook: auto-validates YAML syntax after any .yaml file edit.
# Runs in < 1s. Surfaces parse errors immediately as Claude errors (exit 2)
# so no separate validation tool call is needed.
#
# Token saving: ~1-2 tool calls per YAML edit saved.

PROJ_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Parse file_path from stdin (tool event JSON)
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null || echo "")

# Only act on .yaml files
[[ "$FILE" == *.yaml ]] || exit 0
[[ -f "$FILE" ]] || exit 0

# Fast YAML syntax check (handles !secret, !lambda tags)
python3 - "$FILE" << 'PYEOF'
import yaml, sys
loader = yaml.SafeLoader
loader.add_multi_constructor('', lambda l, t, n: None)
try:
    yaml.load(open(sys.argv[1]), loader)
    print(f"✓ YAML syntax OK: {sys.argv[1]}")
except yaml.YAMLError as e:
    msg = str(e).replace('\n', ' | ')
    print(f"✗ YAML parse error in {sys.argv[1]}: {msg}", file=sys.stderr)
    sys.exit(2)
PYEOF
