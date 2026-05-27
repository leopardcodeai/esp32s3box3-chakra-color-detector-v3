---
description: Create a new feature branch (make feature NAME=<slug>)
---

Create a new feature branch for: $ARGUMENTS

1. Convert the description to a kebab-case slug (e.g. "add timer display" → "add-timer-display")
2. Run: `make feature NAME=<slug>`
3. Confirm the branch was created and remind the user: commit changes, then run `/project:pr`
