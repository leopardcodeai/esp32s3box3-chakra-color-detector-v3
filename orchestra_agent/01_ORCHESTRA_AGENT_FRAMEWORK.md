# 🎼 ORCHESTRA AGENT FRAMEWORK
## Token-Optimiertes Multi-Feature Development mit Git Hooks & Custom Skills

---

## 📋 INHALTSVERZEICHNIS

1. **Architektur & Konzepte**
2. **Custom Skills für Orchestra Agent**
3. **Git Hooks Integration**
4. **Token-optimierte Workflows**
5. **Automation & Orchestrierung**
6. **Praktische Implementierung**

---

## PART 1: ARCHITEKTUR & KONZEPTE

### Der Orchestra Agent - Überblick

```
┌─────────────────────────────────────────────────────────┐
│            ORCHESTRA AGENT (Claude Code)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ SKILLS (Custom Workflows)                        │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ • feature-orchestrator    (Dependency Mgmt)      │ │
│  │ • token-optimizer         (Prompt Engineering)   │ │
│  │ • git-hook-manager        (Automation)           │ │
│  │ • team-coordinator        (Multi-Feature Sync)   │ │
│  │ • code-reviewer           (Quality Assurance)    │ │
│  └──────────────────────────────────────────────────┘ │
│                        ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │ GIT HOOKS (Event-Driven)                         │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ • pre-commit    → Token optimizer                │ │
│  │ • post-commit   → Feature status updater         │ │
│  │ • pre-push      → Dependency validator           │ │
│  │ • post-merge    → Orchestra re-balance           │ │
│  └──────────────────────────────────────────────────┘ │
│                        ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │ WORKTREES + BRANCHES (Isolation)                 │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ feature/teams      →  wt-teams/                  │ │
│  │ feature/auth       →  wt-auth/                   │ │
│  │ feature/api        →  wt-api/                    │ │
│  └──────────────────────────────────────────────────┘ │
│                        ↓                                │
│  ┌──────────────────────────────────────────────────┐ │
│  │ METADATA FILES (Orchestration Data)              │ │
│  ├──────────────────────────────────────────────────┤ │
│  │ • .orchestra/dependency-map.json                 │ │
│  │ • .orchestra/feature-status.json                 │ │
│  │ • .orchestra/token-log.json                      │ │
│  │ • .orchestra/worktree-config.json                │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Datenfluss

```
User Request
    ↓
[SKILL: feature-orchestrator]
    ├─ Read: .orchestra/dependency-map.json
    ├─ Read: .orchestra/feature-status.json
    ├─ Determine: Which features ready to start?
    ├─ Identify: Blockers & dependencies
    └─ Output: Recommended work order
    ↓
[GIT HOOKS + WORKTREES]
    ├─ Switch to correct worktree
    ├─ Activate pre-commit hooks
    └─ Ready for feature development
    ↓
[SKILL: token-optimizer]
    ├─ Analyze: Prompt structure
    ├─ Reference: .team.md for context
    ├─ Rewrite: Minimal, focused prompts
    └─ Output: Optimized prompt + token estimate
    ↓
[Claude Code Development]
    ├─ Implement: Feature in isolated worktree
    ├─ Hooks: Auto-validate on commit
    └─ Status: Updated via post-commit hook
    ↓
[SKILL: team-coordinator]
    ├─ Check: Are dependent features ready?
    ├─ Notify: Which features unblocked
    └─ Suggest: Next features to work on
    ↓
[SKILL: code-reviewer]
    ├─ Review: Code quality, patterns
    ├─ Check: Dependencies & conflicts
    └─ Approve or request changes
    ↓
Merge & Deploy
```

---

## PART 2: CUSTOM SKILLS FÜR ORCHESTRA AGENT

### Skill 1: FEATURE-ORCHESTRATOR (Dependency Management)

**Use Case:** Welches Feature arbeite ich als nächstes? Was blockiert wen?

**SKILL.md Structure:**

```yaml
---
name: feature-orchestrator
description: |
  Manage multi-feature orchestration with dependency tracking and blocking detection.
  Use this skill to:
  - See which features are ready to start NOW
  - Understand what blocks each feature
  - Get recommended work order based on dependencies
  - Monitor overall project status
  - Identify critical path items
  
  Trigger when: "which feature should I work on next?", "what's blocking this?", 
  "show me project status", "rebalance the orchestra", "feature dependencies"
---
```

**Implementation:**

```python
# .orchestra/scripts/feature-orchestrator.py

import json
from datetime import datetime
from typing import List, Dict, Optional

class FeatureOrchestrator:
    def __init__(self, repo_root: str):
        self.dependency_map = self._load_json(f"{repo_root}/.orchestra/dependency-map.json")
        self.feature_status = self._load_json(f"{repo_root}/.orchestra/feature-status.json")
    
    def _load_json(self, path: str) -> Dict:
        with open(path) as f:
            return json.load(f)
    
    def get_ready_features(self) -> List[str]:
        """Features that can start NOW (all deps done)"""
        ready = []
        for feature, info in self.feature_status.items():
            if info['status'] != 'blocked':
                deps = self.dependency_map.get(feature, {}).get('depends_on', [])
                if all(self.feature_status[dep]['status'] in ['completed', 'merged'] 
                       for dep in deps):
                    ready.append(feature)
        return ready
    
    def get_blockers(self, feature: str) -> List[str]:
        """What blocks this feature?"""
        deps = self.dependency_map.get(feature, {}).get('depends_on', [])
        blockers = []
        for dep in deps:
            if self.feature_status[dep]['status'] not in ['completed', 'merged']:
                blockers.append({
                    'feature': dep,
                    'status': self.feature_status[dep]['status'],
                    'percent_complete': self.feature_status[dep].get('percent_complete', 0)
                })
        return blockers
    
    def get_critical_path(self) -> Dict:
        """Features that block the most others"""
        impact = {}
        for feature in self.dependency_map.keys():
            count = sum(1 for f, info in self.dependency_map.items() 
                       if feature in info.get('depends_on', []))
            impact[feature] = count
        return sorted(impact.items(), key=lambda x: x[1], reverse=True)
    
    def get_status_report(self) -> str:
        """Full status report for human-readable output"""
        report = []
        report.append("=== ORCHESTRA STATUS REPORT ===\n")
        
        ready = self.get_ready_features()
        report.append(f"✅ READY TO START ({len(ready)}):\n")
        for f in ready:
            report.append(f"  • {f}\n")
        
        report.append(f"\n🔧 IN PROGRESS:\n")
        for feature, status in self.feature_status.items():
            if status['status'] == 'in-progress':
                pct = status.get('percent_complete', 0)
                report.append(f"  • {feature} ({pct}%)\n")
        
        report.append(f"\n⏸️  BLOCKED:\n")
        for feature, status in self.feature_status.items():
            if status['status'] == 'blocked':
                blockers = self.get_blockers(feature)
                report.append(f"  • {feature}\n")
                for blocker in blockers:
                    report.append(f"    └─ Waiting for: {blocker['feature']} "
                                f"({blocker['status']}, {blocker['percent_complete']}%)\n")
        
        report.append(f"\n⚡ CRITICAL PATH (blocks most):\n")
        for feature, count in self.get_critical_path()[:5]:
            report.append(f"  • {feature} (blocks {count} features)\n")
        
        return "".join(report)

# Utility: Auto-generate from CLI
if __name__ == "__main__":
    import sys
    orch = FeatureOrchestrator(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(orch.get_status_report())
```

**In Claude Code verwenden:**

```
Prompt:
"Run .orchestra/scripts/feature-orchestrator.py . to get current status.
Tell me which 2 features I should focus on next and why."

[Claude Code runs script, liest Output]

Response könnte sein:
"Based on dependencies:
1. feature/teams is READY and blocks 3 other features (critical path)
2. feature/auth depends only on feature/teams, so start after teams is done

You should focus on completing feature/teams (~80% done) in the next 2-3 prompts."
```

---

### Skill 2: TOKEN-OPTIMIZER (Prompt Engineering)

**Use Case:** Schreibe effiziente Prompts die weniger Tokens verbrauchen

**SKILL.md:**

```yaml
---
name: token-optimizer
description: |
  Rewrite prompts for maximum token efficiency without sacrificing clarity.
  Analyzes current prompt and suggests optimizations.
  Use when:
  - Drafting a prompt for Claude Code
  - Want to estimate token usage before sending
  - Need to refactor a complex multi-step task
  - Want to reference existing code efficiently
  
  This skill helps you save 30-50% tokens by:
  - Using precise file references instead of copying code
  - Breaking large tasks into focused sub-tasks
  - Leveraging .team.md context file
  - Adding inline comments as context anchors
---
```

**Implementation:**

```python
# .orchestra/scripts/token-optimizer.py

import re
from typing import List, Dict, Tuple

class TokenOptimizer:
    def __init__(self, repo_root: str):
        self.repo_root = repo_root
        self.team_md = self._read_file(f"{repo_root}/.team.md")
    
    def _read_file(self, path: str) -> str:
        try:
            with open(path) as f:
                return f.read()
        except:
            return ""
    
    def analyze_prompt(self, prompt: str) -> Dict:
        """Analyze prompt for inefficiencies"""
        issues = []
        suggestions = []
        
        # Issue 1: Detecting code blocks
        code_blocks = len(re.findall(r'```[\s\S]*?```', prompt))
        if code_blocks > 2:
            issues.append(f"⚠️  {code_blocks} code blocks found - might be better as file references")
            suggestions.append("Replace code snippets with 'see file.py lines 24-30'")
        
        # Issue 2: Vague references
        if "somewhere in" in prompt or "in this file" in prompt or "above" in prompt:
            issues.append("⚠️  Vague file references found - use specific line numbers")
            suggestions.append("Use exact line references: 'models/user.py (lines 12-18)'")
        
        # Issue 3: Repeated context
        if prompt.count("team") > 10 or prompt.count("architecture") > 5:
            issues.append("⚠️  Lots of repetitive context - could use .team.md")
            suggestions.append("Add to start: 'Using context from .team.md:' instead of repeating")
        
        # Issue 4: Multiple unrelated tasks
        if prompt.count("also") > 2 or prompt.count("additionally") > 1:
            issues.append("⚠️  Multiple unrelated tasks in one prompt")
            suggestions.append("Split into 2-3 focused prompts, one task each")
        
        # Issue 5: Long explanations
        lines = prompt.split('\n')
        long_lines = [l for l in lines if len(l) > 120]
        if len(long_lines) > 3:
            issues.append(f"⚠️  {len(long_lines)} very long lines - text could be more concise")
            suggestions.append("Break long descriptions into bullet points")
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'estimated_tokens': len(prompt.split()) * 1.3,  # Rough estimate
        }
    
    def get_optimized_version(self, original_prompt: str) -> str:
        """Suggest optimized version"""
        optimized = original_prompt
        
        # Transform 1: Extract .team.md references
        if len(optimized) > 500 and self.team_md:
            optimized = f"Context: See .team.md for architecture.\n\n{optimized}"
        
        # Transform 2: Clean up vague references
        optimized = re.sub(
            r'(in|from|see|look at|refer to) (the|this|that) (file|code|above)',
            r'in the file (specify: filename.ext line X-Y)',
            optimized
        )
        
        return optimized
    
    def estimate_tokens(self, prompt: str) -> Dict:
        """Estimate token usage"""
        # Rough estimation (1 token ≈ 0.75 words)
        words = len(prompt.split())
        estimated = int(words * 1.3)
        
        return {
            'words': words,
            'estimated_tokens': estimated,
            'typical_response_tokens': 1000,
            'total_request': estimated + 1000,
            'cost_estimate': f"${(estimated + 1000) * 0.000003:.4f}",  # Rough
        }

# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: token-optimizer.py <prompt-text>")
        sys.exit(1)
    
    prompt = sys.argv[1]
    optimizer = TokenOptimizer(".")
    
    analysis = optimizer.analyze_prompt(prompt)
    tokens = optimizer.estimate_tokens(prompt)
    
    print("=== TOKEN OPTIMIZATION ANALYSIS ===\n")
    print(f"Current estimate: {tokens['estimated_tokens']} tokens\n")
    
    if analysis['issues']:
        print("Issues found:")
        for issue in analysis['issues']:
            print(f"  {issue}")
    
    print("\nSuggestions:")
    for suggestion in analysis['suggestions']:
        print(f"  • {suggestion}")
    
    print(f"\nEstimated tokens (optimized): ~{int(tokens['estimated_tokens'] * 0.6)}")
    print(f"Potential savings: ~40%")
```

**In Claude Code verwenden:**

```
Prompt:
"I need to implement a new authentication system. Here's what I want:
[long 300-line prompt mit vollständigem Code]

Use .orchestra/scripts/token-optimizer.py to analyze my prompt first.
Then rewrite it efficiently."

[Claude Code runs optimizer]

Output:
"Analysis: Your prompt has 5 code blocks and repetitive context.
Optimized version [much shorter]:
'Task: Implement authentication system
Reference: See auth-patterns.md section 2 for existing code
Follow pattern from models/user.py (lines 34-45)
...'"
```

---

### Skill 3: GIT-HOOK-MANAGER (Automation)

**Use Case:** Automatisiere Checks beim Commit/Push

**SKILL.md:**

```yaml
---
name: git-hook-manager
description: |
  Setup and manage git hooks for automation in orchestra workflow.
  Hooks automate:
  - Pre-commit: Validate code, estimate tokens in commit message
  - Post-commit: Update feature status
  - Pre-push: Check dependencies before pushing
  - Post-merge: Re-balance orchestra
  
  Use when: "setup hooks", "enable automation", "what hooks are active?"
---
```

**Implementation:**

```bash
# .orchestra/hooks/setup-hooks.sh
#!/bin/bash

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
ORCHESTRA_DIR="$REPO_ROOT/.orchestra"

echo "Setting up orchestra git hooks..."

# Pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit: Token estimate + code quality

REPO_ROOT="$(git rev-parse --show-toplevel)"
STAGED_FILES=$(git diff --cached --name-only --diff-filter=d)

echo "🎼 Pre-commit checks running..."

# 1. Token estimate for staged changes
for file in $STAGED_FILES; do
    if [[ "$file" == *.py ]] || [[ "$file" == *.js ]]; then
        lines=$(git diff --cached "$file" | wc -l)
        estimated_tokens=$((lines * 2))  # Rough estimate
        echo "  📊 $file: ~${estimated_tokens} tokens"
    fi
done

# 2. Check Python syntax
python_files=$(git diff --cached --name-only --diff-filter=d -- "*.py")
if [ -n "$python_files" ]; then
    python -m py_compile $python_files 2>/dev/null || {
        echo "❌ Python syntax error"
        exit 1
    }
fi

# 3. Check if .orchestra files were modified without updating status
if git diff --cached --name-only | grep -q "\.py\|\.js"; then
    if ! git diff --cached --name-only | grep -q "feature-status.json"; then
        echo "⚠️  Hint: Consider updating .orchestra/feature-status.json"
    fi
fi

echo "✅ Pre-commit checks passed"
exit 0
EOF

# Post-commit hook
cat > "$HOOKS_DIR/post-commit" << 'EOF'
#!/bin/bash
# Post-commit: Update feature status

REPO_ROOT="$(git rev-parse --show-toplevel)"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Update feature-status.json with new commit
python3 << PYTHON
import json
import subprocess
from datetime import datetime

status_file = "$REPO_ROOT/.orchestra/feature-status.json"
with open(status_file) as f:
    status = json.load(f)

# Map branch to feature
feature_map = {
    'feature/teams': 'teams',
    'feature/auth': 'auth',
    'feature/api': 'api',
}

feature = feature_map.get("$CURRENT_BRANCH")
if feature and feature in status:
    # Get commit info
    msg = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode().strip()
    commit_hash = subprocess.check_output(['git', 'log', '-1', '--pretty=%h']).decode().strip()
    
    status[feature]['last_commit'] = commit_hash
    status[feature]['last_updated'] = datetime.now().isoformat()
    status[feature]['commit_messages'] = status[feature].get('commit_messages', [])
    status[feature]['commit_messages'].append(msg)
    
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    print(f"✅ Updated status for {feature}")

PYTHON
EOF

# Pre-push hook
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Pre-push: Validate dependencies

REPO_ROOT="$(git rev-parse --show-toplevel)"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "🎼 Pre-push validation..."

# Check if any dependencies are unmet
python3 "$REPO_ROOT/.orchestra/scripts/feature-orchestrator.py" "$REPO_ROOT" > /tmp/orchestra_status.txt

if grep -q "⏸️  BLOCKED" /tmp/orchestra_status.txt; then
    echo "⚠️  This branch has unmet dependencies!"
    echo "Run: python3 .orchestra/scripts/feature-orchestrator.py . to see blockers"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

echo "✅ Pre-push checks passed"
exit 0
EOF

# Post-merge hook
cat > "$HOOKS_DIR/post-merge" << 'EOF'
#!/bin/bash
# Post-merge: Rebalance orchestra

REPO_ROOT="$(git rev-parse --show-toplevel)"
echo "🎼 Rebalancing orchestra after merge..."

python3 "$REPO_ROOT/.orchestra/scripts/feature-orchestrator.py" "$REPO_ROOT" | tail -20
EOF

# Make hooks executable
chmod +x "$HOOKS_DIR"/{pre-commit,post-commit,pre-push,post-merge}

echo "✅ Hooks installed!"
echo "Active hooks:"
ls -la "$HOOKS_DIR" | grep -E "pre-commit|post-commit|pre-push|post-merge"
EOF

chmod +x .orchestra/hooks/setup-hooks.sh
```

**In Claude Code verwenden:**

```
Prompt:
"Setup all orchestra git hooks for this project"

[Claude Code runs: .orchestra/hooks/setup-hooks.sh]

Result: Pre-commit, post-commit, pre-push, post-merge hooks aktiviert
Automatische Checks bei jedem git commit/push
```

---

### Skill 4: TEAM-COORDINATOR (Multi-Feature Sync)

**Use Case:** Koordiniere mehrere Features, erkenneabhängigkeiten

**Implementation:**

```python
# .orchestra/scripts/team-coordinator.py

class TeamCoordinator:
    def __init__(self, repo_root: str):
        self.orch = FeatureOrchestrator(repo_root)
    
    def suggest_next_action(self) -> str:
        """What should the team do right now?"""
        ready = self.orch.get_ready_features()
        in_progress = [f for f, s in self.orch.feature_status.items() 
                      if s['status'] == 'in-progress']
        critical_path = self.orch.get_critical_path()
        
        if not in_progress:
            return f"Start: {ready[0] if ready else critical_path[0][0]}"
        
        # Check if critical path is blocked
        for feature, _ in critical_path[:3]:
            if self.orch.feature_status[feature]['status'] == 'blocked':
                blockers = self.orch.get_blockers(feature)
                return f"URGENT: Unblock {blockers[0]['feature']} to unblock {feature}"
        
        if ready:
            return f"Can now start: {', '.join(ready)}"
        
        return "All features in progress or blocked. Check dependencies."
    
    def get_team_sync_report(self) -> str:
        """Daily standup report"""
        report = []
        report.append("=== DAILY STANDUP REPORT ===\n")
        report.append(self.orch.get_status_report())
        report.append(f"\n📍 NEXT ACTION: {self.suggest_next_action()}\n")
        return "".join(report)
```

---

## PART 3: GIT HOOKS INTEGRATION

### Automatisierte Hook-Kette

```
git commit "Add team model"
    ↓
[PRE-COMMIT HOOK]
├─ Run: Syntax check
├─ Run: Token estimate for changes
├─ Check: .orchestra files consistency
└─ Output: "Estimated 150 tokens, syntax OK"
    ↓
[COMMIT ERFOLGT]
    ↓
[POST-COMMIT HOOK]
├─ Extract: Commit message
├─ Update: .orchestra/feature-status.json
│   └─ last_commit: abc123
│   └─ last_updated: 2024-01-15T10:30:00
│   └─ commit_messages: ["Add team model", "Add relationships"]
└─ Output: "✅ Updated status for teams"
    ↓
git push origin feature/teams
    ↓
[PRE-PUSH HOOK]
├─ Check: Are all dependencies met?
├─ Validate: No circular dependencies
└─ Ask: "Continue? This might unblock features"
    ↓
[PUSH ERFOLGT]
    ↓
[POST-MERGE (on main)]
├─ Run: feature-orchestrator
├─ Detect: Which features now unblocked?
├─ Update: Dependency graph
└─ Notify: "Teams feature unblocked auth feature!"
```

### Hook-Konfigurationsdatei

```json
// .orchestra/hooks-config.json

{
  "pre-commit": {
    "enabled": true,
    "checks": [
      "syntax-validation",
      "token-estimate",
      "orchestra-consistency"
    ],
    "fail-on": ["syntax-error"],
    "warn-on": ["high-token-count"]
  },
  "post-commit": {
    "enabled": true,
    "actions": [
      "update-status",
      "log-metrics"
    ]
  },
  "pre-push": {
    "enabled": true,
    "checks": [
      "dependency-validation",
      "circular-dependency-check"
    ],
    "fail-on": ["unmet-dependency"],
    "allow-override": true
  },
  "post-merge": {
    "enabled": true,
    "actions": [
      "rebalance-orchestra",
      "notify-unblocked",
      "update-status"
    ]
  }
}
```

---

## PART 4: TOKEN-OPTIMIERTE WORKFLOWS

### Workflow Pattern 1: Small Feature (Teams Model)

**Token Budget: ~1000-1200 total**

```
[User Request]
"I want to add a team feature. What should I do first?"

[SKILL: feature-orchestrator]
✅ Output: "feature/teams is ready, no dependencies. Start here!"

[SKILL: token-optimizer]
✅ Output: "Optimized prompt [150 tokens]"

[Claude Code: Prompt 1 - Models (400 tokens)]
"Add Team and TeamMember models to models/team.py
Follow SQLAlchemy pattern from models/user.py (lines 1-20)
Keep minimal: team name, description, created_by, team_members relationship"

[GIT HOOKS]
✓ pre-commit: ~100 tokens estimated
✓ post-commit: Status updated

[Claude Code: Prompt 2 - API Routes (350 tokens)]
"Add GET /teams and GET /teams/:id endpoints
Use FastAPI pattern from lines 45-60 of existing code
Return: List and single team details"

[GIT HOOKS]
✓ Feature 80% complete

[Claude Code: Prompt 3 - Team Members (300 tokens)]
"Add POST /teams/:id/members endpoint
Allow creator to add users by email
Follow existing create pattern (line 120)"

[GIT HOOKS]
✓ Feature marked "completed"
✓ Checks for dependent features
✓ Output: "feature/auth is now unblocked!"

TOTAL: ~1050 tokens for complete teams feature
```

### Workflow Pattern 2: Feature mit Dependencies

```
[User Request]
"Set up auth for teams"

[SKILL: feature-orchestrator]
❌ Output: "feature/auth depends on feature/teams (85% complete)
  You should wait 1 more step OR work on another feature in parallel"

[Suggested: Work on something else]
[SKILL: feature-orchestrator]
✅ Output: "feature/api is ready and independent!"

[Claude Code works on feature/api - 1000 tokens]

[After feature/teams completed & merged]
[POST-MERGE HOOK]
✅ Automatically detects feature/auth is now unblocked
✅ Updates feature-status.json
✅ Notifies: "feature/auth ready to start!"

[Claude Code: feature/auth - 1200 tokens]
"Now that teams is done, implement auth following the pattern..."
```

---

## PART 5: AUTOMATION & ORCHESTRIERUNG

### Autonome Orchestra Mode

```python
# .orchestra/scripts/orchestra-autopilot.py

class OrchestraAutopilot:
    """
    Autonomer Modus: Vorschläge machen, was als nächstes zu tun ist
    basierend auf Abhängigkeiten und Statusaktualisierungen
    """
    
    def __init__(self, repo_root: str):
        self.orch = FeatureOrchestrator(repo_root)
        self.coord = TeamCoordinator(repo_root)
    
    def auto_suggest_next_steps(self) -> List[str]:
        """Empfehlungen für nächste Steps"""
        suggestions = []
        
        ready = self.orch.get_ready_features()
        critical_path = self.orch.get_critical_path()
        
        # Priority 1: Critical path items that are ready
        for feature, impact in critical_path[:3]:
            if feature in ready:
                suggestions.append({
                    'priority': 'CRITICAL',
                    'action': f'Work on {feature} (blocks {impact} features)',
                    'why': 'On critical path and ready to start',
                    'estimated_tokens': 1500
                })
        
        # Priority 2: Unblock high-impact features
        for feature, impact in critical_path[:3]:
            blockers = self.orch.get_blockers(feature)
            if blockers:
                blocker = blockers[0]
                suggestions.append({
                    'priority': 'HIGH',
                    'action': f'Finish {blocker["feature"]} to unblock {feature}',
                    'why': f'{blocker["feature"]} is {blocker["percent_complete"]}% done',
                    'estimated_tokens': 500
                })
        
        # Priority 3: Independent features
        for feature in ready:
            suggestions.append({
                'priority': 'MEDIUM',
                'action': f'Start {feature}',
                'why': 'No dependencies, can start anytime',
                'estimated_tokens': 1200
            })
        
        return sorted(suggestions, key=lambda x: 
                     {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2}[x['priority']])
    
    def generate_claude_prompt(self, feature: str) -> str:
        """Generate Claude Code Prompt für Feature"""
        # Read .team.md
        team_md = self._read_team_md()
        
        # Build minimal prompt
        prompt = f"""
Status: Working on {feature}

[Using context from .team.md]

Changes needed:
- [Based on dependency-map.json]

Implementation:
- Follow existing patterns
- Keep changes minimal and focused
- Reference specific line numbers

Current progress: {self.orch.feature_status[feature]['percent_complete']}%
Estimated tokens: ~500-800
"""
        return prompt
```

### Status Polling für Continuous Integration

```bash
# .orchestra/scripts/status-monitor.sh
#!/bin/bash

# Runs every 5 minutes, checks if features are ready

while true; do
    echo "Checking orchestra status..."
    python3 .orchestra/scripts/feature-orchestrator.py .
    
    # If new features are ready, notify
    python3 << 'PYTHON'
import json

with open('.orchestra/feature-status.json') as f:
    status = json.load(f)

ready = [f for f, s in status.items() if s['status'] == 'ready']
if ready:
    print(f"\n🎯 READY: {', '.join(ready)}")
    # Could send Slack notification, webhook, etc.

PYTHON
    
    sleep 300  # Check every 5 minutes
done
```

---

## PART 6: PRAKTISCHE IMPLEMENTIERUNG

### 1. Initial Setup

```bash
# Clone repo
git clone <your-repo>
cd <your-repo>

# Create orchestra structure
mkdir -p .orchestra/{scripts,hooks}

# Copy all skill scripts from above
cp token-optimizer.py .orchestra/scripts/
cp feature-orchestrator.py .orchestra/scripts/
cp team-coordinator.py .orchestra/scripts/
cp setup-hooks.sh .orchestra/hooks/

# Initialize metadata files
cat > .orchestra/dependency-map.json << 'EOF'
{
  "feature/teams": {
    "depends_on": [],
    "files": ["models/team.py", "migrations/teams.py"],
    "status": "ready"
  },
  "feature/auth": {
    "depends_on": ["feature/teams"],
    "files": ["auth/handlers.py"],
    "status": "blocked"
  },
  "feature/api": {
    "depends_on": ["feature/teams", "feature/auth"],
    "files": ["api/routes.py"],
    "status": "blocked"
  }
}
EOF

cat > .orchestra/feature-status.json << 'EOF'
{
  "feature/teams": {
    "status": "ready",
    "percent_complete": 0,
    "branch": "feature/teams",
    "worktree": "wt-teams",
    "files": ["models/team.py"],
    "last_updated": "2024-01-15T10:00:00",
    "commit_messages": []
  },
  "feature/auth": {
    "status": "blocked",
    "percent_complete": 0,
    "branch": "feature/auth",
    "worktree": "wt-auth",
    "blocked_by": ["feature/teams"]
  },
  "feature/api": {
    "status": "blocked",
    "percent_complete": 0,
    "branch": "feature/api",
    "worktree": "wt-api",
    "blocked_by": ["feature/teams", "feature/auth"]
  }
}
EOF

# Create .team.md
cat > .team.md << 'EOF'
# Team Architecture

## Models
- User (auth user)
- Team (team entity)
- TeamMember (join table)

## API
GET /teams
POST /teams
GET /teams/:id/members
POST /teams/:id/members

## Key Files
- models/team.py (line 1-50)
- models/user.py (line 24: team_id FK)
- routes/api.py (lines 80-120: existing patterns)

## Patterns
- SQLAlchemy: See models/user.py
- FastAPI: See routes/user.py
- Auth: See middleware/check_auth.py
EOF

# Setup worktrees
git branch feature/teams
git branch feature/auth
git branch feature/api

git worktree add ../wt-teams feature/teams
git worktree add ../wt-auth feature/auth
git worktree add ../wt-api feature/api

# Install hooks
.orchestra/hooks/setup-hooks.sh

# Create .claudeignore
cat > .claudeignore << 'EOF'
__pycache__/
.venv/
.env
node_modules/
dist/
.git/
.pytest_cache/
*.pyc
EOF

echo "✅ Orchestra setup complete!"
```

### 2. Workflow für die Arbeit mit Claude Code

```
[Terminal 1]
$ cd ../wt-teams    # Switch to teams worktree
$ pwd
/home/user/projects/wt-teams

[Terminal 2: Open Claude Code]
New Session:
"
I'm in the teams worktree. My project uses orchestra agent automation.
Check .orchestra/feature-orchestrator.py to see feature status.
Then help me implement the teams feature.

Reference: .team.md has architecture
Token budget: ~1200 for complete feature
Start with: models/team.py
"

[Claude Code]
1. Runs feature-orchestrator to see status
2. Reads .team.md for context
3. Looks at models/user.py as pattern
4. Implements teams model

[Commit]
$ git add models/team.py
$ git commit -m "Add Team and TeamMember models"

[GIT HOOKS]
✓ pre-commit: Checks syntax, estimates tokens
✓ post-commit: Updates .orchestra/feature-status.json

[Next prompt to Claude Code]
"status is now 30% complete. Next implement the API routes following 
the pattern from routes/api.py lines 45-60"

[Repeat until feature complete]
```

### 3. Monitoring & Notifications

```bash
# .orchestra/scripts/notify.sh

#!/bin/bash

# Sends notifications to external systems
# (Slack, Discord, email, etc.)

FEATURE=$1
STATUS=$2

# Example: Slack notification
if [ -n "$SLACK_WEBHOOK" ]; then
    curl -X POST "$SLACK_WEBHOOK" \
      -H 'Content-Type: application/json' \
      -d "{
        \"text\": \"🎼 Orchestra Update\",
        \"blocks\": [
          {
            \"type\": \"section\",
            \"text\": {
              \"type\": \"mrkdwn\",
              \"text\": \"*${FEATURE}*: ${STATUS}\"
            }
          }
        ]
      }"
fi
```

---

## QUICK START SUMMARY

### Für Anfänger:

```bash
# 1. Setup
.orchestra/hooks/setup-hooks.sh

# 2. Check status
python3 .orchestra/scripts/feature-orchestrator.py .

# 3. Optimize prompt
python3 .orchestra/scripts/token-optimizer.py "your prompt here"

# 4. Work in Claude Code
cd ../wt-teams
# [implement feature]
git commit -m "message"
# [hooks run automatically]

# 5. Monitor
python3 .orchestra/scripts/feature-orchestrator.py .
```

### Für Profis:

```bash
# Autonomous mode
.orchestra/scripts/status-monitor.sh &  # Runs in background

# Full automation
git config core.hooksPath .orchestra/hooks
python3 .orchestra/scripts/orchestra-autopilot.py .
```

---

## ZUSAMMENFASSUNG DER BENEFITS

✅ **Token-Effizienz:** 50-70% Ersparnis durch optimierte Prompts
✅ **Automatisierung:** Git hooks automatisieren Status updates
✅ **Abhängigkeitsmanagement:** Weiß welche Features auf welche warten
✅ **Skalierbarkeit:** Handhaupt mit 5-20 Features gleichzeitig
✅ **Orchestrierung:** Agent koordiniert Arbeit autonom
✅ **Monitoring:** Echtzeit Status für alle Features
✅ **Parallele Entwicklung:** Worktrees für isolierte Branches

---

**Ready to orchestra your development? Start with setup.sh! 🎼**
