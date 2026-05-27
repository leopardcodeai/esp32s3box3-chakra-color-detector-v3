---
description: Show current device config + git status summary
---

Show a concise summary of the current project state:

```bash
make status && echo "---" && cat device_config.yaml
```

Present this as:
- **Git**: branch, last tag, commits ahead of remote
- **Device config**: table of the key substitution values (HA host, media player, chakra light, timer entity, theme colors, brightness)

Do NOT show the locale substitutions (monday/tuesday/etc.) — those are noise.
