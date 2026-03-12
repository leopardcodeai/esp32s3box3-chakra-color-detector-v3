# Orchestra Agent - Praktische Setup & Config Dateien

Hier sind alle Dateien, die du für dein Orchestra System benötigst.

---

## 1. SETUP SCRIPT: `setup-orchestra.sh`

Kopiere diese datei zu: `.orchestra/setup-orchestra.sh`

```bash
#!/bin/bash

# setup-orchestra.sh
# Initialize Orchestra Agent framework in your repo

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
ORCHESTRA_DIR="$REPO_ROOT/.orchestra"

echo "🎼 Initializing Orchestra Agent Framework..."

# Create directory structure
mkdir -p "$ORCHESTRA_DIR"/{scripts,hooks,config}

# 1. Create dependency-map.json
echo "📋 Creating dependency-map.json..."
cat > "$ORCHESTRA_DIR/dependency-map.json" << 'EOF'
{
  "feature/teams": {
    "depends_on": [],
    "files": ["models/team.py", "migrations/001_teams.py"],
    "description": "Team model and management",
    "status": "ready"
  },
  "feature/auth": {
    "depends_on": ["feature/teams"],
    "files": ["auth/handlers.py", "auth/middleware.py"],
    "description": "Team-based authentication",
    "status": "blocked"
  },
  "feature/api": {
    "depends_on": ["feature/teams", "feature/auth"],
    "files": ["api/routes.py", "api/schemas.py"],
    "description": "REST API for teams",
    "status": "blocked"
  }
}
EOF

# 2. Create feature-status.json
echo "📊 Creating feature-status.json..."
cat > "$ORCHESTRA_DIR/feature-status.json" << 'EOF'
{
  "feature/teams": {
    "status": "ready",
    "percent_complete": 0,
    "branch": "feature/teams",
    "worktree": "wt-teams",
    "files": [],
    "last_updated": "2024-01-15T10:00:00",
    "commit_messages": [],
    "last_commit": null
  },
  "feature/auth": {
    "status": "blocked",
    "percent_complete": 0,
    "branch": "feature/auth",
    "worktree": "wt-auth",
    "files": [],
    "blocked_by": ["feature/teams"],
    "last_updated": "2024-01-15T10:00:00",
    "commit_messages": []
  },
  "feature/api": {
    "status": "blocked",
    "percent_complete": 0,
    "branch": "feature/api",
    "worktree": "wt-api",
    "files": [],
    "blocked_by": ["feature/teams", "feature/auth"],
    "last_updated": "2024-01-15T10:00:00",
    "commit_messages": []
  }
}
EOF

# 3. Create hooks-config.json
echo "⚙️  Creating hooks-config.json..."
cat > "$ORCHESTRA_DIR/hooks-config.json" << 'EOF'
{
  "pre-commit": {
    "enabled": true,
    "checks": ["syntax-validation", "token-estimate", "orchestra-consistency"],
    "fail-on": ["syntax-error"],
    "warn-on": ["high-token-count"]
  },
  "post-commit": {
    "enabled": true,
    "actions": ["update-status", "log-metrics"]
  },
  "pre-push": {
    "enabled": true,
    "checks": ["dependency-validation"],
    "fail-on": ["unmet-dependency"],
    "allow-override": true
  },
  "post-merge": {
    "enabled": true,
    "actions": ["rebalance-orchestra", "notify-unblocked"]
  }
}
EOF

# 4. Create token-log.json for tracking
echo "💰 Creating token-log.json..."
cat > "$ORCHESTRA_DIR/token-log.json" << 'EOF'
{
  "total_tokens_budgeted": 50000,
  "total_tokens_used": 0,
  "features": {
    "feature/teams": {
      "budgeted": 1500,
      "used": 0,
      "sessions": []
    },
    "feature/auth": {
      "budgeted": 2000,
      "used": 0,
      "sessions": []
    },
    "feature/api": {
      "budgeted": 1500,
      "used": 0,
      "sessions": []
    }
  }
}
EOF

# 5. Create .team.md
echo "📚 Creating .team.md..."
cat > "$REPO_ROOT/.team.md" << 'EOF'
# Team Architecture & Reference

## Overview

This document serves as the single source of truth for architecture and patterns.
Reference this in Claude Code prompts instead of copying/explaining.

## Database Models

### User Model
- File: `models/user.py` (lines 12-50)
- Fields: id, email, password_hash, created_at
- Key: Use SQLAlchemy ORM pattern with `Column`, `relationship`

### Team Model
- File: `models/team.py` (to be created)
- Fields: id, name, description, created_by, team_members
- Pattern: Follow User model structure

### TeamMember (Join Table)
- File: `models/team.py` (with Team)
- Fields: user_id FK, team_id FK, role, joined_at
- Pattern: Use same relationship pattern as group_members (models/group.py line 45)

## API Patterns

### GET Endpoints
- Pattern: `routes/api.py` lines 45-60
- Structure: Query model, validate auth, return JSON
- Error codes: 200 OK, 401 Unauthorized, 404 Not Found

### POST Endpoints
- Pattern: `routes/api.py` lines 65-85
- Structure: Validate input (Pydantic), create object, return created object
- Error codes: 201 Created, 400 Bad Request, 401 Unauthorized

### Pydantic Schemas
- Pattern: `schemas/` directory
- File: `schemas/team.py` (to be created)
- Reference: `schemas/user.py` for pattern

## Authentication

### JWT Tokens
- Handler: `auth/handlers.py` lines 20-40
- Payload: user_id, team_id, exp
- Storage: HTTP Authorization header

### Middleware
- File: `middleware/check_auth.py`
- Pattern: Extract JWT, validate, attach to request context

### Routes Protection
- Import: `from middleware.check_auth import require_auth`
- Usage: `@app.get("/teams", dependencies=[require_auth])`

## Key File Locations

```
models/
  ├── user.py          (existing)
  ├── team.py          (to create)
  └── __init__.py

routes/
  ├── api.py           (existing)
  └── __init__.py

schemas/
  ├── user.py          (existing)
  ├── team.py          (to create)
  └── __init__.py

auth/
  ├── handlers.py      (existing)
  ├── middleware.py    (existing)
  └── __init__.py

migrations/
  ├── 001_teams.py     (to create)
  └── __init__.py
```

## Dependencies

- SQLAlchemy 1.4+
- FastAPI
- Pydantic
- Python 3.8+

## Common Patterns

### Adding a Foreign Key
1. Import: `from sqlalchemy import ForeignKey`
2. Add column: `team_id = Column(Integer, ForeignKey("teams.id"))`
3. Add relationship: `team = relationship("Team")`

### Creating API Endpoint
1. Import route: `from fastapi import APIRouter, Depends`
2. Create router: `router = APIRouter(prefix="/teams")`
3. Add endpoint: `@router.get("/", response_model=List[TeamSchema])`
4. Implement: Handle auth, query, return

### Database Migration
1. Create file: `migrations/NNN_description.py`
2. Implement: `upgrade()` and `downgrade()` functions
3. Run: Migration tool (Alembic, etc)

## Status & Notes

- feature/teams: Ready to start
- feature/auth: Blocked by teams (waiting for Team model)
- feature/api: Blocked by both (needs models + auth)

Updated: 2024-01-15
EOF

# 6. Create .claudeignore
echo "🚫 Creating .claudeignore..."
cat > "$REPO_ROOT/.claudeignore" << 'EOF'
# Files to ignore when providing to Claude Code

# Python
__pycache__/
*.pyc
*.pyo
.Python
.venv/
env/
venv/
.env
.pytest_cache/

# Node
node_modules/
npm-debug.log
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Git
.git/
.gitignore

# Build
dist/
build/
*.egg-info/

# OS
.DS_Store
Thumbs.db
EOF

# 7. Setup git branches and worktrees
echo "🌿 Setting up git branches and worktrees..."

# Check if branches exist
if ! git rev-parse --verify feature/teams > /dev/null 2>&1; then
    git branch feature/teams
    echo "  ✅ Created branch: feature/teams"
fi

if ! git rev-parse --verify feature/auth > /dev/null 2>&1; then
    git branch feature/auth main  # auth depends on teams
    echo "  ✅ Created branch: feature/auth"
fi

if ! git rev-parse --verify feature/api > /dev/null 2>&1; then
    git branch feature/api main  # api depends on both
    echo "  ✅ Created branch: feature/api"
fi

# Create worktrees (skip if they exist)
PARENT_DIR="$(dirname "$REPO_ROOT")"

for wt in wt-teams wt-auth wt-api; do
    if [ ! -d "$PARENT_DIR/$wt" ]; then
        branch="feature/${wt#wt-}"
        git worktree add "$PARENT_DIR/$wt" "$branch"
        echo "  ✅ Created worktree: $wt"
    fi
done

# 8. Install git hooks
echo "🔗 Installing git hooks..."
bash "$ORCHESTRA_DIR/setup-hooks.sh"

# 9. Initialize python scripts
echo "🐍 Installing Python helpers..."
python3 << 'PYTHON'
import os
import json

# Verify all config files exist
orchestra_dir = ".orchestra"
required_files = [
    "dependency-map.json",
    "feature-status.json",
    "hooks-config.json",
    "token-log.json"
]

for fname in required_files:
    path = os.path.join(orchestra_dir, fname)
    if os.path.exists(path):
        print(f"  ✅ {fname}")
    else:
        print(f"  ❌ {fname} - MISSING")

PYTHON

echo ""
echo "✅ Orchestra Agent Framework initialized!"
echo ""
echo "📖 Next steps:"
echo "  1. Review .orchestra/dependency-map.json and adjust features"
echo "  2. Review .team.md and update with your actual code patterns"
echo "  3. Start developing in worktrees:"
echo "     cd ../wt-teams"
echo "  4. Use Claude Code with Skills:"
echo "     - feature-orchestrator (check status)"
echo "     - token-optimizer (optimize prompts)"
echo "  5. Commits automatically update status via hooks"
echo ""
echo "💡 To get started:"
echo "  cd ../wt-teams"
echo "  echo 'Open Claude Code here and ask for help with feature/teams'"
```

---

## 2. GIT HOOKS: `setup-hooks.sh`

Kopiere diese datei zu: `.orchestra/setup-hooks.sh`

```bash
#!/bin/bash

# setup-hooks.sh
# Install all git hooks for Orchestra automation

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
ORCHESTRA_DIR="$REPO_ROOT/.orchestra"

echo "🔗 Installing Orchestra git hooks..."

# PRE-COMMIT: Token estimate + syntax check
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
STAGED=$(git diff --cached --numstat | wc -l)

if [ "$STAGED" -gt 0 ]; then
    echo "🎼 Pre-commit: Checking $STAGED file(s)..."
    
    # Token estimate
    LINES=$(git diff --cached | wc -l)
    TOKENS=$((LINES * 2))
    echo "  📊 Estimated tokens: ~$TOKENS"
    
    # Python syntax check
    PYTHON_FILES=$(git diff --cached --name-only --diff-filter=d -- "*.py")
    if [ -n "$PYTHON_FILES" ]; then
        python3 -m py_compile $PYTHON_FILES 2>/dev/null || {
            echo "  ❌ Python syntax error"
            exit 1
        }
    fi
fi
exit 0
EOF

chmod +x "$HOOKS_DIR/pre-commit"
echo "  ✅ pre-commit hook installed"

# POST-COMMIT: Update feature status
cat > "$HOOKS_DIR/post-commit" << 'EOF'
#!/bin/bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
ORCHESTRA_DIR="$REPO_ROOT/.orchestra"

if [[ "$CURRENT_BRANCH" == feature/* ]]; then
    python3 << PYTHON
import json
from datetime import datetime
import subprocess

feature_name = "$CURRENT_BRANCH".replace("feature/", "")
status_file = "$ORCHESTRA_DIR/feature-status.json"

try:
    with open(status_file) as f:
        status = json.load(f)
    
    if "$CURRENT_BRANCH" in status:
        commit_hash = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=%h']
        ).decode().strip()
        
        status["$CURRENT_BRANCH"]['last_commit'] = commit_hash
        status["$CURRENT_BRANCH"]['last_updated'] = datetime.now().isoformat()
        
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        print(f"✅ Updated: {feature_name}")
except Exception as e:
    print(f"⚠️  Could not update status: {e}")
PYTHON
fi
EOF

chmod +x "$HOOKS_DIR/post-commit"
echo "  ✅ post-commit hook installed"

# PRE-PUSH: Check dependencies
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
ORCHESTRA_DIR="$REPO_ROOT/.orchestra"

echo "🎼 Pre-push: Validating dependencies..."

python3 << PYTHON
import json

try:
    with open("$ORCHESTRA_DIR/dependency-map.json") as f:
        deps = json.load(f)
    
    with open("$ORCHESTRA_DIR/feature-status.json") as f:
        status = json.load(f)
    
    for feature, config in deps.items():
        depends_on = config.get('depends_on', [])
        for blocker in depends_on:
            if blocker in status:
                if status[blocker]['status'] not in ['completed', 'merged']:
                    print(f"⚠️  {feature} depends on {blocker}")
                    print(f"   {blocker} status: {status[blocker]['status']}")
    
    print("✅ Dependency check passed")
except Exception as e:
    print(f"⚠️  Could not validate: {e}")
    print("   Continuing anyway...")
PYTHON

exit 0
EOF

chmod +x "$HOOKS_DIR/pre-push"
echo "  ✅ pre-push hook installed"

# POST-MERGE: Rebalance orchestra
cat > "$HOOKS_DIR/post-merge" << 'EOF'
#!/bin/bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
ORCHESTRA_DIR="$REPO_ROOT/.orchestra"

echo "🎼 Post-merge: Checking for unblocked features..."

python3 << PYTHON
import json

try:
    with open("$ORCHESTRA_DIR/dependency-map.json") as f:
        deps = json.load(f)
    
    with open("$ORCHESTRA_DIR/feature-status.json") as f:
        status = json.load(f)
    
    # Check what's now unblocked
    for feature, config in deps.items():
        depends_on = config.get('depends_on', [])
        
        # Check if all dependencies are met
        if depends_on and all(status.get(d, {}).get('status') in 
                             ['completed', 'merged'] for d in depends_on):
            if status.get(feature, {}).get('status') == 'blocked':
                print(f"✅ UNBLOCKED: {feature}")
                status[feature]['status'] = 'ready'
    
    # Save updated status
    with open("$ORCHESTRA_DIR/feature-status.json", 'w') as f:
        json.dump(status, f, indent=2)
        
except Exception as e:
    print(f"⚠️  Rebalance check failed: {e}")
PYTHON

EOF

chmod +x "$HOOKS_DIR/post-merge"
echo "  ✅ post-merge hook installed"

echo ""
echo "✅ All hooks installed successfully!"
```

---

## 3. TOKEN-TRACKING: `token-log.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Orchestra Token Log",
  "type": "object",
  "properties": {
    "total_tokens_budgeted": {
      "type": "integer",
      "description": "Total token budget for entire project"
    },
    "total_tokens_used": {
      "type": "integer",
      "description": "Total tokens actually used"
    },
    "features": {
      "type": "object",
      "patternProperties": {
        "^feature/.*": {
          "type": "object",
          "properties": {
            "budgeted": { "type": "integer" },
            "used": { "type": "integer" },
            "sessions": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "date": { "type": "string", "format": "date-time" },
                  "tokens": { "type": "integer" },
                  "task": { "type": "string" },
                  "prompt_summary": { "type": "string" }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

---

## 4. WORKTREE-CONFIG: `worktree-config.json`

```json
{
  "worktrees": {
    "wt-teams": {
      "branch": "feature/teams",
      "path": "../wt-teams",
      "feature": "teams",
      "status": "ready",
      "depends_on": []
    },
    "wt-auth": {
      "branch": "feature/auth",
      "path": "../wt-auth",
      "feature": "auth",
      "status": "blocked",
      "depends_on": ["teams"]
    },
    "wt-api": {
      "branch": "feature/api",
      "path": "../wt-api",
      "feature": "api",
      "status": "blocked",
      "depends_on": ["teams", "auth"]
    }
  },
  "current_worktree": "wt-teams",
  "last_updated": "2024-01-15T10:00:00"
}
```

---

## 5. COMMAND-LINE HELPERS

Kopiere in: `.orchestra/bin/` directory

### `orchestra-status.sh`
```bash
#!/bin/bash
python3 .orchestra/scripts/feature-orchestrator.py .
```

### `orchestra-optimize.sh`
```bash
#!/bin/bash
python3 .orchestra/scripts/token-optimizer.py "$@"
```

### `orchestra-log.sh`
```bash
#!/bin/bash
python3 << 'PYTHON'
import json

with open('.orchestra/token-log.json') as f:
    log = json.load(f)

print("=== TOKEN USAGE LOG ===\n")
print(f"Budget: {log['total_tokens_budgeted']}")
print(f"Used: {log['total_tokens_used']}")
print(f"Remaining: {log['total_tokens_budgeted'] - log['total_tokens_used']}")
print()

for feature, data in log['features'].items():
    print(f"{feature}:")
    print(f"  Budgeted: {data['budgeted']}")
    print(f"  Used: {data['used']}")
    print(f"  Remaining: {data['budgeted'] - data['used']}")
PYTHON
```

---

## USAGE

```bash
# Initialize everything
bash .orchestra/setup-orchestra.sh

# After that, use these commands:
.orchestra/bin/orchestra-status.sh      # See what's ready
.orchestra/bin/orchestra-optimize.sh "your prompt"  # Optimize
.orchestra/bin/orchestra-log.sh         # See token usage

# In Claude Code:
# "Run .orchestra/scripts/feature-orchestrator.py . and tell me..."
# "Optimize my prompt using token-optimizer"
```

---

**All files ready to copy into your project!**
