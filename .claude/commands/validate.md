---
description: Run ESPHome config validation (make validate)
---

Run `make validate` in the project root to validate the ESPHome configuration.

```bash
make validate 2>&1
```

If validation fails, show the full error output and identify which YAML key or lambda is causing it.
If validation passes, confirm with "✓ Configuration is valid" and show the last line of output.
