---
description: Run GPIO pin conflict and strapping pin check
---

Run the GPIO pin validator:

```bash
make pins 2>&1
```

If conflicts are found, show the conflicting pins and which components are fighting over them.
If strapping pin warnings are found, note which GPIOs (0, 3, 45, 46) and whether `ignore_strapping_warning: true` is set.
If all clear, confirm "✓ All pin checks passed — safe to deploy".
