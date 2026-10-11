---
name: token-optimizer
description: |
  Rewrite prompts for maximum token efficiency without sacrificing clarity or completeness.
  Analyzes current prompt for inefficiencies and suggests optimizations.
  Use when:
  - Drafting a prompt for Claude Code to implement a feature
  - Want to estimate token usage BEFORE sending large prompt
  - Need to refactor a complex multi-step task into focused prompts
  - Want to reference existing code efficiently instead of copying
  - Have a long prompt and want to compress it
  
  This skill helps save 30-50% tokens by:
  - Using precise file references ("see models/user.py lines 24-30") instead of pasting code
  - Breaking large tasks into focused sub-tasks
  - Leveraging .team.md context file instead of explaining
  - Using inline code comments as context anchors
  
  Trigger when: "optimize my prompt", "estimate tokens", "compress this prompt",
  "how many tokens will this use?", "make this more efficient", "better way to ask this?"
  "improve this prompt", "too many tokens?"
---

# Token Optimizer Skill

## Overview

Token Optimizer helps you write Claude Code prompts that are **shorter, clearer, and more efficient**. It analyzes what you're trying to ask and suggests better phrasing that saves 30-50% tokens while getting better results.

## Why Token Efficiency Matters

A typical multi-feature development with Orchestra Agent uses:
- **Inefficient prompts:** 4000-5000 tokens per feature
- **Optimized prompts:** 1200-1500 tokens per feature

**50+ features in a project = 190,000+ tokens saved!**

## How Token Optimizer Works

### Step 1: Analyze Your Prompt
```
Input: Your current prompt (any length)
↓
Scanner detects:
  - Code blocks (better as references)
  - Vague references (need line numbers)
  - Repetitive context (use .team.md)
  - Multiple unrelated tasks (split them)
  - Overly long explanations (shorten)
↓
Output: List of issues + suggestions
```

### Step 2: Optimize
```
Issues found:
  ❌ 3 code blocks pasted (200 tokens)
  ❌ Vague: "in the function above"
  ❌ Repeating architecture twice
  ❌ 5 different tasks in one prompt
  
Suggestions:
  ✅ Replace code with references
  ✅ Use line numbers instead
  ✅ Say "using .team.md context"
  ✅ Split into 5 small prompts
  
Result: 450 tokens → 150 tokens (67% savings!)
```

### Step 3: Estimate Tokens
```
Before: 
  450 tokens estimated
  ~$0.0015 per prompt

After:
  150 tokens estimated
  ~$0.0005 per prompt
  
Savings: 300 tokens, $0.001 per prompt
```

## Using Token Optimizer in Claude Code

### Pattern 1: Before Writing a Prompt

```
Prompt to Claude Code:
"I want to implement team authentication. Users login, 
get JWT, use it to access team endpoints. I have a User model 
[copies 50 lines] and need to extend it with [more copy]. 
Also add email verification [more copy]. And make sure 
tokens expire after 24 hours [more details]..."

Better: First optimize
"Use token-optimizer to analyze my prompt idea and tell me 
the best way to ask this in 3-4 small prompts instead of one big one"

Claude Code Response:
"Your idea is good but the way you asked it would use ~600 tokens.
Here's a better structure (150 tokens per prompt):

Prompt 1: 'Add authentication models'
Prompt 2: 'Implement login endpoint'
Prompt 3: 'Add token expiration logic'
Prompt 4: 'Email verification'

Total: 600 tokens → 400 tokens saved!"
```

### Pattern 2: Optimize Existing Prompts

```
You already have a prompt written:
"Add a new feature that extends the User model with team support. 
The User should have a team_id foreign key. I also need a Team model 
with team_members relationship. Plus I need API endpoints for creating 
teams and adding members. [10 more sentences of explanation]"

Use optimizer:
"Here's my prompt, optimize it for token efficiency"

Claude Code Response:
"Current estimate: 280 tokens
Optimized estimate: 90 tokens (68% savings!)

Your prompt:
BEFORE: 'Add a new feature that extends the User model with 
team support. The User should have a team_id foreign key...'

OPTIMIZED: 'Task: Add team_id FK to User and create Team model
Reference: Follow pattern from models/user.py (lines 1-20)
Minimal implementation: user team_id, Team class, team_members relationship'"
```

### Pattern 3: Estimate Before Large Prompts

```
Planning a complex feature:
"I'm about to write a detailed prompt for auth + teams integration. 
Tell me the estimated token cost and suggest if I should split it."

Claude Code Response:
"Your planned prompt would be ~800 tokens. 
Better approach: Split into 2 prompts of 300 + 350 tokens each.
Total: 800 → 650 tokens saved. Ready?"
```

## Token-Saving Techniques

### Technique 1: Use File References Instead of Copy-Paste

❌ **Inefficient (200+ tokens):**
```
"I have this User model:

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    # ... 40 more lines ...

Now add similar fields to Team model..."
```

✅ **Efficient (10 tokens):**
```
"Create Team model following pattern from models/user.py (lines 12-50)
Add: id, name, description, created_by"
```

**Savings:** ~190 tokens for same information!

### Technique 2: Reference .team.md Instead of Explaining

❌ **Inefficient (300+ tokens):**
```
"Our architecture uses SQLAlchemy ORM with FastAPI.
We have these models:
- User: authentication users
- Project: belongs to one user
- Task: belongs to one project
- Comment: belongs to one task

API structure:
GET /users/:id - get user
GET /projects - list projects
POST /projects - create project
[... 20 more lines explaining ...]"
```

✅ **Efficient (5 tokens):**
```
"Using context from .team.md for architecture.
Implement: Team model and API endpoints"
```

**Savings:** ~295 tokens!

### Technique 3: Use Inline Comments as Anchors

Instead of explaining, add comments in code:

```python
# models/team.py

class Team(Base):
    __tablename__ = "teams"
    
    # PATTERN: Follow User model structure (models/user.py line 15)
    id = Column(Integer, Primary_Key)
    name = Column(String)
    
    # DEPENDS: team_members uses same join pattern as 
    # group_members (models/group.py line 45)
    team_members = relationship("TeamMember")
```

Then in Claude Code prompt:
```
"Implement TeamMember model.
Follow PATTERN comment (line 15) for structure.
Follow DEPENDS comment (line 18) for relationship pattern."
```

**Savings:** 100+ tokens by letting comments carry context!

### Technique 4: Break Into Tiny Focused Prompts

❌ **Inefficient (1200 tokens one big prompt):**
```
"I need to implement complete team system:
1. Create Team and TeamMember models
2. Add foreign key to User model
3. Create API endpoints (GET /teams, POST /teams, etc)
4. Add authentication checks on endpoints
5. Add email validation
6. Add error handling
[... more details ...]"
```

✅ **Efficient (3 prompts × 200-300 tokens = 600-900 total):**
```
Prompt 1 (150 tokens): "Create Team and TeamMember models"
Prompt 2 (200 tokens): "Add API endpoints for teams"
Prompt 3 (150 tokens): "Add auth checks and validation"
```

**Savings:** 300-600 tokens!

**Rule:** One focused task per prompt = 30-50% token savings

### Technique 5: Use Constraints Instead of Examples

❌ **Inefficient (400+ tokens with examples):**
```
"Add team member invitations. 
Here's an example of what I mean:
[detailed explanation of email sent, token created, ...]
The user should receive an email like:
[full email template]
When they click the link:
[what happens]
..."
```

✅ **Efficient (50 tokens with constraints):**
```
"Add team member invitations.
Constraints:
- Send email with invite link (use existing email template)
- Link valid for 7 days
- One-click accept, adds to team_members"
```

**Savings:** ~350 tokens!

## Hands-On Examples

### Example 1: Small Feature (Teams Model)

**Before (400 tokens):**
```
"I want to add team support to my app. Here's the User model...
[pastes User code]
I need a similar Team model with these fields: name, description, 
created_by. Then I need a join table for team members because users 
can be in multiple teams. Use SQLAlchemy like the User model does...
[explains pattern in detail]
Also make sure to import the necessary modules at the top...
[more details]"
```

**After (120 tokens):**
```
"Add Team and TeamMember models to models/team.py
Follow SQLAlchemy pattern from models/user.py (lines 1-20)
Fields: Team(id, name, description, created_by, team_members rel)
        TeamMember(user_id FK, team_id FK, role)"
```

**Savings: 280 tokens (70%)**

### Example 2: API Implementation

**Before (550 tokens):**
```
"I need REST API endpoints for teams:
1. GET /teams - returns list of all teams for current user
2. POST /teams - creates new team, current user is owner
3. GET /teams/:id - returns single team details
4. POST /teams/:id/members - adds member to team

For each endpoint, I need:
- Parameter validation using Pydantic schemas
- Authentication check (JWT token)
- Error handling (team not found, not member, etc)
- Proper HTTP status codes (200 for success, 400 for bad input, etc)

Here's the pattern I'm using for other endpoints...
[pastes 80 lines of code]
Please follow the same pattern..."
```

**After (180 tokens):**
```
"Add endpoints in routes/api.py:
- GET /teams (auth required)
- POST /teams (auth required, creator is owner)
- GET /teams/:id (member only)
- POST /teams/:id/members (owner only)

Reference: Follow pattern from models/routes.py (lines 45-60)
Use: Pydantic schemas from schemas/team.py"
```

**Savings: 370 tokens (67%)**

### Example 3: Complex Feature

**Before (1200 tokens):**
```
"Implement authentication system for teams:

First, I need to understand our current setup...
[explains entire auth system in 300 tokens]

Here's what I want to add:
[describes team auth in 400 tokens]

The implementation should:
[lists 10 requirements in 200 tokens]

Here's how other parts of the system do it:
[pastes example code in 300 tokens]"
```

**After (3 prompts × 250 tokens = 750 tokens):**
```
Prompt 1: "Add team_id to JWT token payload. Reference: middleware/jwt.py"
Prompt 2: "Add team_id check to endpoint middleware. Pattern: line 34"  
Prompt 3: "Add team membership validation to endpoints"
```

**Savings: 450 tokens (38%)**

## Interactive Optimization Session

### Scenario: You have a vague idea

```
You: "I want to add notifications to teams"

Claude Code (using token-optimizer):
"Let me think about this. Notifications could mean:
1. Email notifications (new member, updates, etc)
2. In-app notifications (shown on dashboard)
3. Real-time notifications (websocket)
4. Batch notifications (daily digest)

Which one? Or multiple? This affects how I'd suggest breaking it down."

You: "Start with email notifications"

Claude Code:
"Got it. Here's my suggested prompt structure:

Prompt 1: Create NotificationEvent model
Prompt 2: Email service for sending notifications
Prompt 3: Trigger email on team events
Prompt 4: Template system for emails

Estimated tokens: 4 × 250 = 1000 tokens

Ready to start with Prompt 1?"
```

## Tips & Tricks

### Tip 1: Estimate Tokens While Planning
Before writing any code, estimate what the whole feature will cost:
```
"Estimate tokens for implementing team notifications:
- Models + migrations: ~200
- Email service: ~300
- Endpoints: ~250
- Tests: ~200
Total: ~950 tokens"
```

### Tip 2: Identify Token Killers
```
"What's costing the most tokens in my current workflow?
- Copying code: 40%
- Explaining architecture: 35%
- Listing requirements: 15%
- Other: 10%"
```

### Tip 3: Optimize Between Sessions
```
"I used 1800 tokens on feature/auth last week.
How could I do it more efficiently this time?"
```

### Tip 4: Compare Approaches
```
"I have 2 ways to ask this. Which uses fewer tokens?
Approach A: [prompt 1]
Approach B: [prompt 2]"
```

## Rules for Token Optimization

1. **Use references, not copy-paste:** "see file.py lines X-Y" not full code
2. **Use .team.md:** Never explain architecture, reference the doc
3. **Break into focused prompts:** One task per prompt minimum
4. **Add inline comments:** Let code comments carry context
5. **Use constraints:** Describe limits, not with examples
6. **Specific references:** Always use exact line numbers
7. **Assume context:** Assume Claude knows your codebase structure

## When NOT to Optimize

- Simple questions don't need optimization (e.g., "what's this line?")
- Exploratory work might need more tokens (that's ok)
- Novel or complex work might need more explanation (that's ok)

**Only optimize for repetitive, well-understood tasks.**

## Troubleshooting

### "Optimized prompt is too vague"
→ Add more constraints or reference more specific lines

### "I keep explaining architecture in every prompt"
→ Expand and maintain .team.md, reference it instead

### "My prompts don't save tokens"
→ Check you're not pasting full files - use line references

### "Claude doesn't understand shortened reference"
→ Use EXACT line numbers and file paths

## See Also
- `feature-orchestrator` - Manage dependencies
- `git-hook-manager` - Automate status updates
- `.team.md` - Architecture reference (create this file!)

---

**Pro tip: Save tokens → save money, faster development!**
