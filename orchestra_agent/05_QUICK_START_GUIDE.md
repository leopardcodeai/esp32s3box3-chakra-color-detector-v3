# 🎼 ORCHESTRA AGENT - QUICK START GUIDE

Alles was du brauchst um sofort zu starten!

---

## 5 MINUTEN SETUP

### Schritt 1: Projekt klonen
```bash
git clone https://github.com/your-repo
cd your-repo
```

### Schritt 2: Orchestra initialisieren
```bash
# Kopiere die setup-orchestra.sh in dein Repo
curl -o .orchestra/setup-orchestra.sh https://[your-raw-url]/setup-orchestra.sh

# Führe aus
bash .orchestra/setup-orchestra.sh
```

✅ Erledigt! Alle Branches, Worktrees, Hooks und Config-Dateien sind eingerichtet.

### Schritt 3: First Feature Branch öffnen
```bash
cd ../wt-teams    # Wechsle zu teams worktree
pwd               # Bestätige: /home/user/projects/wt-teams
git status        # Bestätige: on branch feature/teams
```

### Schritt 4: Claude Code öffnen (im wt-teams Directory)

```
Öffne Claude Code Terminal hier und schreib:

"Setup: I'm in the teams worktree of a project with Orchestra Agent.
Run .orchestra/scripts/feature-orchestrator.py . to check status.
What should I implement first?"

[Claude Code antwortet mit Status und Empfehlung]
```

---

## DIE ERSTE FEATURE: TEAMS MODEL (Beispiel)

### Phase 1: Status Check & Planning

**Claude Code Prompt:**
```
Status check:
- I'm in wt-teams worktree
- Run: .orchestra/scripts/feature-orchestrator.py .
- Tell me: What's the current status? Is feature/teams ready to work on?
```

**Claude Code Response:**
```
✅ READY TO START (1):
  • feature/teams

🔧 IN PROGRESS: (none)

⏸️ BLOCKED (2):
  • feature/auth (blocked by: feature/teams, 0% complete)
  • feature/api (blocked by: feature/teams, feature/auth)

⚡ CRITICAL PATH:
  • feature/teams (blocks 2 features - highest priority)

→ RECOMMENDATION: Start with feature/teams. It blocks auth and api.
  Estimated work: 3-4 prompts, ~1200 tokens total.
```

### Phase 2: Token Optimization

**Claude Code Prompt:**
```
Before I start coding, optimize my development approach for token efficiency.

Here's what I want to implement:
1. Team model with id, name, description, created_by
2. TeamMember join table for many-to-many relationship  
3. API endpoints for create/read teams
4. Authentication checks on endpoints

Estimate tokens and suggest best prompt order.
```

**Claude Code Response:**
```
Analysis of your plan:

Inefficient approach (1 big prompt): ~800 tokens
Optimized approach (4 small prompts): ~600 tokens saved!

Here's the optimal order:

Prompt 1: "Models" (150 tokens)
  Task: Create Team and TeamMember models
  Reference: .team.md, models/user.py pattern
  
Prompt 2: "API Routes" (200 tokens)
  Task: Add GET/POST /teams endpoints
  Reference: routes/api.py pattern (lines 45-60)
  
Prompt 3: "Team Members" (150 tokens)
  Task: Add POST /teams/:id/members endpoint
  Reference: Existing relationship patterns
  
Prompt 4: "Auth Checks" (100 tokens)
  Task: Add authentication to endpoints
  Reference: middleware/check_auth.py

Total: ~600 tokens. Ready to start?
```

### Phase 3: Prompt 1 - Models

**Claude Code Prompt:**
```
Task: Create Team and TeamMember models for teams feature

File: models/team.py (create new file)

Reference: .team.md and models/user.py (lines 12-50) for patterns

Models needed:
1. Team class:
   - id: Integer primary key
   - name: String, unique, not null
   - description: String
   - created_by: Integer FK to User
   - team_members: Relationship to TeamMember

2. TeamMember class:
   - user_id: Integer FK to User
   - team_id: Integer FK to Team
   - role: String (default "member")
   - joined_at: DateTime

Keep minimal. No API or complex logic yet - just models.

Estimated tokens: 150
```

**Development Output:**
```python
# models/team.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from datetime import datetime

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    team_members = relationship("TeamMember", cascade="all, delete-orphan")
    creator = relationship("User")

class TeamMember(Base):
    __tablename__ = "team_members"
    
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    role = Column(String, default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)
```

**After Implementation:**
```bash
git add models/team.py
git commit -m "Add Team and TeamMember models"

# GIT HOOKS run automatically:
# ✅ Pre-commit: Syntax OK, ~120 tokens
# ✅ Post-commit: Status updated to 25%
```

### Phase 4: Prompt 2 - API Routes

**Claude Code Prompt:**
```
Task: Add team API endpoints

File: routes/api.py

Add these endpoints:
1. GET /teams
   - Return: List of all teams for current user
   - Auth: Required
   - Response: List[TeamSchema]

2. POST /teams
   - Create new team, current user is creator
   - Auth: Required
   - Input: name, description
   - Response: TeamSchema

3. GET /teams/:id
   - Return team details
   - Auth: Required, user must be member
   - Response: TeamSchema

Reference: Existing endpoint pattern in routes/api.py (lines 45-60)
Use: TeamSchema from schemas/team.py

Minimal implementation, no fancy features yet.

Estimated tokens: 200
```

**After Implementation:**
```bash
git add routes/api.py schemas/team.py migrations/001_teams.py
git commit -m "Add team API endpoints (GET/POST)"

# GIT HOOKS:
# ✅ Pre-commit: Syntax OK, ~180 tokens
# ✅ Post-commit: Status updated to 50%
```

### Phase 5: Prompt 3 - Team Members Endpoint

**Claude Code Prompt:**
```
Task: Add POST /teams/:id/members endpoint

File: routes/api.py

Endpoint needed:
- POST /teams/:id/members
- Add user to team
- Input: user_email (find user by email)
- Auth: Required, only team creator can add members
- Response: Updated team with members list
- Error: 404 if team not found, 400 if user not found

Reference: Similar pattern in routes/api.py for group members
Keep implementation simple.

Estimated tokens: 150
```

**After Implementation:**
```bash
git add routes/api.py
git commit -m "Add team members endpoint"

# GIT HOOKS:
# ✅ Pre-commit: Syntax OK, ~100 tokens
# ✅ Post-commit: Status updated to 75%
```

### Phase 6: Prompt 4 - Authentication

**Claude Code Prompt:**
```
Task: Add authentication checks to team endpoints

File: routes/api.py

Add auth checks:
1. GET /teams - Require JWT auth
2. POST /teams - Require JWT auth
3. GET /teams/:id - Require JWT auth AND user must be team member
4. POST /teams/:id/members - Require JWT auth AND user must be team creator

Use: @require_auth decorator from middleware/check_auth.py

Reference: How it's done in user endpoints (lines 80-95)
Keep it simple, reuse existing auth patterns.

Estimated tokens: 100
```

**After Implementation:**
```bash
git add routes/api.py
git commit -m "Add auth checks to team endpoints"

# GIT HOOKS:
# ✅ Pre-commit: Syntax OK, ~80 tokens
# ✅ Post-commit: Status updated to 100% ✅

# POST-MERGE DETECTION:
# When you merge to main, hooks detect:
# ✅ feature/teams is COMPLETED
# ✅ feature/auth is NOW UNBLOCKED!
# ✅ feature/api still waiting for auth
```

---

## WÄHREND DER ENTWICKLUNG

### Monitoring - Was ist der Status?

```bash
# Jederzeit checken:
python3 .orchestra/scripts/feature-orchestrator.py .

Output:
✅ READY TO START (1):
  • feature/api (if teams and auth are done)

🔧 IN PROGRESS (1):
  • feature/auth (after you merge teams)

⏸️ BLOCKED: (0)

→ You've unblocked feature/auth! Start working there next.
```

### Problem: Stuck / Can't Continue?

```bash
# Check was blockiert dich
python3 .orchestra/scripts/feature-orchestrator.py .

Falls du blockiert bist:
- Merge teams to main first
- Check ob dependencies wirklich complete sind
- Update .orchestra/feature-status.json manuell falls nötig
```

### Token Tracking

```bash
# Siehe wieviele Tokens du für dieses Feature verbraucht hast
cat .orchestra/token-log.json

{
  "feature/teams": {
    "budgeted": 1500,
    "used": 650,      # 4 prompts × ~150-200 tokens
    "sessions": [
      { "date": "2024-01-15T...", "tokens": 150, "task": "models" },
      { "date": "2024-01-15T...", "tokens": 200, "task": "api" },
      // ...
    ]
  }
}

→ Du bist bei 650/1500 tokens = 43% des Budgets
→ Noch 850 tokens für finetuning, tests, refinement
```

---

## NACH FEATURE COMPLETION: Feature/Auth starten

### Schritt 1: Merge zu Main

```bash
cd ../wt-teams
git add .
git commit -m "Complete: teams feature ready"
git push origin feature/teams

# Auf GitHub: Create Pull Request → Merge to main

# POST-MERGE HOOK LÄUFT AUTOMATISCH:
# ✅ Erkennt: feature/teams wurde gemerged
# ✅ Updated: feature-status.json
# ✅ Output: "feature/auth is NOW UNBLOCKED!"
```

### Schritt 2: Starte feature/auth

```bash
cd ../wt-auth
git pull origin feature/auth    # Aktualisiere branch

# Neue Claude Code Session
"
I'm in wt-auth worktree. Feature teams just completed and merged.
Run orchestrator to confirm auth is unblocked.
Then help me implement team-based authentication.
"

Claude Code:
"✅ feature/auth is UNBLOCKED! 
 Dependencies met:
 - feature/teams: ✅ COMPLETED and MERGED

Ready to implement. Feature/auth depends on Team model.
Estimated work: 3 prompts, ~1500 tokens.

Should I start?"
```

---

## FORTGESCHRITTENERE SZENARIEN

### Scenario 1: 3 Features parallel (Große Teams)

```
Dein Team hat 3 Developer:
- Developer 1: working on feature/teams (in wt-teams)
- Developer 2: waiting for feature/auth (in wt-auth)
- Developer 3: working on something else (in wt-api - but blocked)

STATUS: Run orchestrator
├─ Ready: feature/teams (Dev 1 working)
├─ Blocked: feature/auth (waiting for teams, Dev 2 waiting)
└─ Blocked: feature/api (waiting for both, Dev 3 waiting)

ACTION: While Dev 1 works on teams:
- Dev 2 can START designing auth (without waiting for models)
- Dev 3 can write API tests (without implementation)

Once teams is DONE:
- Dev 2 starts implementing auth (uses Team model)
- Dev 3 can now start API implementation
```

### Scenario 2: Feature nicht auf kritischem Pfad

```
Du hast Features:
├─ feature/teams (blocks: auth, api) ⚡ CRITICAL
├─ feature/auth (blocks: api)
├─ feature/notifications (blocks: nothing) 
└─ feature/api (blocks: nothing)

ORCHESTRATOR SAGT:
"feature/teams blocks 2 others = CRITICAL PATH
 feature/notifications is independent and ready!
 
 You could either:
 A) Continue with teams (critical path)
 B) Work on notifications (independent, could help other teams)
 C) Both in parallel if you have resources"

CHOICE: Meist A (finish critical path zuerst)
```

### Scenario 3: Dependency Conflict

```
Problem: Feature A depends on Feature B
         Feature B now depends on Feature A (circular!)

ORCHESTRATOR ERKENNT:
❌ Circular dependency detected!
   feature/teams → feature/auth → feature/teams
   
FIX: .orchestra/dependency-map.json anpassen

{
  "feature/teams": { "depends_on": [] },        // Clean
  "feature/auth": { "depends_on": ["teams"] }   // Clean
}
```

---

## TIPPS & TRICKS

### Tipp 1: Committen oft, aber fokussiert

```bash
# ❌ FALSCH: Einen großen Commit
git add .
git commit -m "Teams feature"

# ✅ RICHTIG: Mehrere kleine Commits
git add models/team.py
git commit -m "Add Team model"

git add routes/api.py
git commit -m "Add team endpoints"

git add migrations/
git commit -m "Add team migration"

Warum: Jeder commit triggert post-commit hook
→ Status wird mehrmals updated
→ Progress ist sichtbar
→ Einfacher zu debuggen wenn etwas falsch läuft
```

### Tipp 2: .team.md ist dein bester Freund

```
Lass Claude Code immer auf .team.md referenzieren:

❌ "I have this architecture... [explains for 300 tokens]"

✅ "Using .team.md context. Follow the patterns there."

→ Spart ~100-200 tokens pro prompt!
```

### Tipp 3: Incremental Progress Tracking

```bash
# Update feature-status.json manuell für besseres Tracking

Nach Models: 25%
"feature/teams": { "percent_complete": 25 }

Nach API: 50%
"feature/teams": { "percent_complete": 50 }

Nach Validation: 75%
"feature/teams": { "percent_complete": 75 }

Nach Tests: 100%
"feature/teams": { "percent_complete": 100 }

Vorteil: Andere können sehen wo du stehst
```

### Tipp 4: Reuse Patterns

```
Einmal ein Pattern schreiben, dan mültiplicar:

Pattern 1: User Model + API
→ Create Team Model + API (same pattern)
→ Create Project Model + API (same pattern)
→ Create Task Model + API (same pattern)

Token spend:
- User: 1200 tokens (Pattern definieren)
- Team: 800 tokens (Pattern nutzen, 33% sparen)
- Project: 800 tokens (Pattern nutzen, 33% sparen)
- Task: 800 tokens (Pattern nutzen, 33% sparen)

Total: 3600 tokens vs. 4800 ohne reuse = 25% sparen!
```

---

## CHECKLISTE: Feature Complete

Bevor du Feature mergest:

- [ ] Code implementiert
- [ ] Git hooks laufen erfolgreich
- [ ] feature-status.json shows 100%
- [ ] Tests passen (wenn relevant)
- [ ] Code in wt-XXX sieht gut aus
- [ ] Alle Commits haben gute Messages
- [ ] Pull Request ist erstellt
- [ ] Code Review ist done (wenn relevant)
- [ ] Ready for merge!

```bash
# Final check
python3 .orchestra/scripts/feature-orchestrator.py .
git log --oneline -10
cat .orchestra/feature-status.json | grep feature/teams -A5
```

---

## TROUBLESHOOTING

| Problem | Lösung |
|---------|---------|
| "My branch is missing" | `git branch feature/teams` dann `git worktree add ../wt-teams feature/teams` |
| "Hooks not running" | `bash .orchestra/setup-hooks.sh` to reinstall |
| "Status not updating" | Manually edit `.orchestra/feature-status.json` |
| "Circular dependencies" | Remove problematic dependency from dependency-map.json |
| "Token estimate seems wrong" | It's an approximation. Don't rely on it 100%. |
| "Can't push due to dependencies" | Answer "y" to the pre-push hook prompt to override |
| "Too many tokens used" | Check token-log.json, next feature should be more efficient |

---

## NÄCHSTE SCHRITTE NACH FIRST FEATURE

1. ✅ Complete feature/teams (~1200 tokens)
2. ✅ Merge to main
3. ✅ Start feature/auth (now unblocked)
4. ✅ Complete feature/auth (~2000 tokens)
5. ✅ Merge to main
6. ✅ Start feature/api (now unblocked)
7. Continue with more features...

**Result:** Structured development, tracked dependencies, optimized tokens!

---

**Du bist jetzt ein Orchestra Agent! 🎼**

Viel Erfolg bei deinem nächsten Feature! 🚀
