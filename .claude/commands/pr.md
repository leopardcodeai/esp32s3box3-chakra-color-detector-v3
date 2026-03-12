---
description: Push current branch and open a draft PR
---

1. Check current branch: `cd /Users/alexanderbrunker/esp/esphome_device && git rev-parse --abbrev-ref HEAD`
2. If on `main`, stop and tell the user to create a feature branch first with `/project:feature`
3. Otherwise run: `cd /Users/alexanderbrunker/esp/esphome_device && make pr 2>&1`
4. Show the PR URL and remind: "CI will validate the ESPHome config. Run `/project:merge` when CI is green."
