---
name: feature-orchestrator
description: |
  Manage multi-feature orchestration with dependency tracking for Claude Code development.
  Use this skill to:
  - See which features are ready to start NOW (all dependencies met)
  - Understand what BLOCKS each feature and why
  - Get recommended work order based on critical path analysis
  - Monitor overall project orchestration status
  - Identify which features unblock others (impact analysis)
  
  Trigger when user asks: "which feature should I work on next?", "what blocks this feature?", 
  "show me project status", "what's the critical path?", "what unblocks what?",
  "orchestration status", "feature dependencies", "rebalance orchestra"
  
  This skill is part of Orchestra Agent Framework for multi-feature, low-token development.
---

# Feature Orchestrator Skill

## Overview

The Feature Orchestrator manages dependencies and scheduling for multi-feature development. It prevents you from working on blocked features and suggests optimal work order based on what blocks the most other features (critical path).

## Data Files

This skill relies on two JSON files in your repo:

**`.orchestra/dependency-map.json`** - Defines relationships between features
```json
{
  "feature/teams": {
    "depends_on": [],
    "files": ["models/team.py"],
    "status": "ready"
  },
  "feature/auth": {
    "depends_on": ["feature/teams"],
    "files": ["auth/handlers.py"]
  }
}
```

**`.orchestra/feature-status.json`** - Tracks current progress
```json
{
  "feature/teams": {
    "status": "in-progress",
    "percent_complete": 45,
    "branch": "feature/teams",
    "last_updated": "2024-01-15T10:30:00"
  }
}
```

## Commands

### Get Full Status Report
```bash
python3 .orchestra/scripts/feature-orchestrator.py .
```

Output shows:
- ✅ READY (features you can start now)
- 🔧 IN PROGRESS (current work)
- ⏸️ BLOCKED (waiting for dependencies)
- ⚡ CRITICAL PATH (features blocking the most)

### Check What Blocks A Feature
```bash
# In your prompt to Claude Code:
"Check what blocks feature/auth using feature-orchestrator.py"
```

Script will show:
```
feature/auth is blocked by:
  • feature/teams (in-progress, 45% complete)
```

### Get Recommended Work Order
```bash
# In Claude Code prompt:
"Run feature-orchestrator and tell me which 3 features I should 
focus on in order of importance. Explain why."
```

Claude will analyze:
1. Which features are ready (no blockers)
2. Which features block the most others
3. Recommend best work order to unblock maximum features

## When to Use This Skill

### Before Starting Work
```
User: "What should I implement next?"

Response: Check status → "feature/teams is ready and blocks 3 features (critical path). 
Start here. feature/auth is blocked by teams, so tackle it after."
```

### When Features Seem Stuck
```
User: "I can't work on feature/api right now"

Response: Check blockers → "feature/api depends on feature/teams (30% done) and 
feature/auth (not started). Finish teams first, then can start auth."
```

### After Finishing a Feature
```
User: "Just merged feature/teams, what's unblocked?"

Response: Rerun orchestrator → "Excellent! feature/auth is now unblocked. 
feature/api still waiting for both teams and auth."
```

### During Team Standups
```
Daily standup: Run full status report to see:
- What's blocked, what's ready
- Who should work on what
- Critical path items
```

## Integration with Claude Code

### Pattern 1: Start of Session
```
New Claude Code session in wt-teams worktree:

"Run .orchestra/scripts/feature-orchestrator.py . and tell me:
1. What's the current status?
2. Is teams feature ready to work on?
3. What should I implement first?"
```

### Pattern 2: Mid-Development Check
```
After implementing models, before API routes:

"Use feature-orchestrator to check if any other features are 
now unblocked by what I just did."
```

### Pattern 3: Multi-Feature Coordination
```
When managing 5+ features:

"Orchestrator shows auth is blocked by teams. Teams is 80% done.
Should I start auth now or finish something else?"
```

## Key Concepts

### Ready Features
Features with **NO unmet dependencies**. All dependencies must be either:
- "completed" status (fully done)
- "merged" status (merged to main)

### Blocked Features
Features with **unmet dependencies**. Can't start until all dependencies reach "completed" or "merged".

### Critical Path
Features that **block the most other features**. Prioritize these:
- Completing feature/teams unblocks feature/auth AND feature/api (impact: 2)
- Completing feature/auth unblocks feature/api (impact: 1)

**Rule:** Always work on highest-impact features first (critical path).

### Percent Complete
Track progress in feature-status.json:
- 0-25%: Models/structure done
- 25-50%: Core implementation done
- 50-75%: API/routes done
- 75-100%: Testing and refinement

## Updating Status

The skill is **read-only** for Claude. Status updates happen via:

1. **Git hooks** (automatic):
   - Post-commit hook updates last_updated and commits
   - Pre-merge hook detects completed features

2. **Manual updates** (if needed):
```bash
# Edit .orchestra/feature-status.json
vim .orchestra/feature-status.json

# Update percent_complete for current branch
"feature/teams": {
  "status": "in-progress",
  "percent_complete": 75,  # <-- Update this
  "last_updated": "2024-01-15T11:00:00"
}
```

## Tips & Tricks

### Tip 1: High-Level View
```
"Orchestrator, show me a simple summary:
- How many features ready?
- How many blocked? Why?
- What's the top 3 I should focus on?"
```

### Tip 2: Dependency Chain Analysis
```
"What's the shortest path to unblock feature/api?
What features must complete in order?"
```

### Tip 3: Parallel Work
```
"Orchestrator shows 3 features ready. 
I have 3 developers. What should each one work on?"
```

### Tip 4: Blocked Feature Workarounds
```
"Feature/auth is blocked by teams. Can I design auth endpoints 
without waiting for the teams feature to be complete?"
```

## Example Workflow

```
Session 1:
$ cd ../wt-teams
Claude Code: "Use orchestrator to check current status"
→ "teams is ready and critical path. Start here"

Claude Code: "Implement teams model"
[Implement + commit]
Post-commit hook: Updates status to 25%

Session 2:
$ cd ../wt-teams
Claude Code: "Implement teams API endpoints"
[Implement + commit]
Post-commit hook: Updates status to 50%

Session 3:
$ cd ../wt-teams
Claude Code: "Final: validation and tests"
[Implement + commit]
Post-commit hook: Updates status to 100%

After merge to main:
Post-merge hook: Sets feature/teams to "merged"
Orchestrator: "feature/auth is NOW UNBLOCKED!"

Session 4:
$ cd ../wt-auth
Claude Code: "Orchestrator shows I can now start auth"
[Implementation begins]
```

## Troubleshooting

### "Feature shows as blocked but should be ready"
→ Check `.orchestra/feature-status.json` - parent feature might show as "in-progress" instead of "completed"

### "Orchestrator says ready but feature isn't really ready"
→ Manually mark feature as "completed" if it's actually done but hook didn't update

### "Circular dependency detected"
→ There's a cycle: A depends on B, B depends on A. Fix dependency-map.json.

## See Also
- `token-optimizer` - Optimize prompts for token efficiency
- `git-hook-manager` - Setup automated status updates
- `team-coordinator` - Coordinate multiple developers

---

**Use orchestrator constantly to avoid wasted effort on blocked features!**
