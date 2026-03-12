---
description: Merge the current feature branch PR (squash + delete branch)
---

1. Check CI status: `cd /Users/alexanderbrunker/esp/esphome_device && gh pr view --json statusCheckRollup -q '.statusCheckRollup[] | "\(.name): \(.conclusion)"' 2>&1`
2. If CI is still pending, tell the user to wait
3. If CI failed, show which check failed and suggest fixing it
4. If CI passed, run: `cd /Users/alexanderbrunker/esp/esphome_device && make merge 2>&1`
5. After merge, show the new tag (if auto-tagged by release.yml) and confirm the branch was deleted
