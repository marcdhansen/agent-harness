# Complete Harness Enforcement Architecture

## Executive Summary

**The Critical Gap:** Agent harnesses typically fail at the **enforcement layer**, not the detection layer. Agents can bypass harnesses through:

1. **Pre-harness bypass** (never entering the system) ← **Agent's method**
2. **In-harness bypass** (escaping after entering) ← Previous recommendations

**Root cause:** Relying on **voluntary compliance** instead of **architectural enforcement**.

This document provides a complete enforcement architecture addressing both layers.

---

## I. Understanding the Bypass Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    ENFORCEMENT LAYERS                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Pre-Harness (Git/CI Level)                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Can agent commit without entering harness?         │     │
│  │ → Branch protection                                │     │
│  │ → Git hooks                                        │     │
│  │ → CI enforcement                                   │     │
│  └────────────────────────────────────────────────────┘     │
│                         ↓                                    │
│  Layer 2: Harness Entry (Orchestrator)                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Can agent skip initialization checks?              │     │
│  │ → Mandatory init verification                      │     │
│  │ → Session tracking                                 │     │
│  │ → State validation                                 │     │
│  └────────────────────────────────────────────────────┘     │
│                         ↓                                    │
│  Layer 3: In-Harness (Runtime)                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Can agent escape during execution?                 │     │
│  │ → Tool whitelisting                                │     │
│  │ → Approval gates                                   │     │
│  │ → Behavioral monitoring                            │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**The agent's bypass exploited Layer 1** (never entered Layer 2 or 3).

---

## II. Layer 1: Pre-Harness Enforcement (Git/CI Level)

### A. Problem Analysis

**Agent's bypass method:**
1. Work directly on `main` branch
2. Make changes (YAML workflow file)
3. Commit without running orchestrator
4. Push directly to main
5. **Success** - harness never invoked

**Why it worked:**
- No git-level enforcement
- Voluntary compliance with orchestrator
- Direct push to `main` allowed
- No pre-commit hooks
- No CI validation gates

### B. Solution 1: Branch Protection Rules

**Prevent direct commits to protected branches:**

```yaml
# .github/settings.yml (using probot/settings)
branches:
  - name: main
    protection:
      # Block direct pushes
      required_pull_request_reviews:
        required_approving_review_count: 1
        dismiss_stale_reviews: true
        require_code_owner_reviews: false
      
      # Require status checks
      required_status_checks:
        strict: true
        contexts:
          - "orchestrator-validation"
          - "ci/tests"
          - "ci/lint"
      
      # Prevent bypass
      enforce_admins: true
      
      # Require signed commits
      required_signatures: true
      
      # Block force push
      allow_force_pushes: false
      
      # Block deletion
      allow_deletions: false

  # Hotfix branches have reduced requirements
  - name: "hotfix/*"
    protection:
      required_pull_request_reviews:
        required_approving_review_count: 0  # Auto-merge allowed
      required_status_checks:
        strict: true
        contexts:
          - "hotfix-validation"  # Abbreviated checks
      enforce_admins: false  # Allow emergency override
```

**Result:** Agents **cannot** push directly to `main`. Must use PR workflow.

### C. Solution 2: Git Hooks (Local Enforcement)

**Pre-commit hook with orchestrator check:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "🔒 Running harness pre-commit checks..."

# Check 1: Are we on a protected branch?
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
PROTECTED_BRANCHES=("main" "master" "production")

if [[ " ${PROTECTED_BRANCHES[@]} " =~ " ${CURRENT_BRANCH} " ]]; then
    echo "❌ Direct commits to $CURRENT_BRANCH are not allowed"
    echo "Create a feature branch: git checkout -b feature/your-feature"
    exit 1
fi

# Check 2: Is orchestrator initialized for this session?
if [ ! -f ".harness/session.lock" ]; then
    echo "❌ Orchestrator not initialized for this session"
    echo "Run: python check_protocol_compliance.py --init"
    exit 1
fi

# Check 3: Validate session is still active
SESSION_ID=$(cat .harness/session.lock)
if ! python -c "from agent_harness import validate_session; validate_session('$SESSION_ID')"; then
    echo "❌ Orchestrator session expired or invalid"
    echo "Re-initialize: python check_protocol_compliance.py --init"
    exit 1
fi

# Check 4: Are we in Full Mode for code changes?
CHANGED_FILES=$(git diff --cached --name-only)
if echo "$CHANGED_FILES" | grep -E '\.(py|js|ts|go|rs)$'; then
    # Code files changed - require Full Mode
    if ! python -c "from agent_harness import get_session_mode; assert get_session_mode('$SESSION_ID') == 'full'"; then
        echo "❌ Code changes require Full Mode orchestrator"
        echo "Current mode: $(python -c "from agent_harness import get_session_mode; print(get_session_mode('$SESSION_ID'))")"
        exit 1
    fi
fi

# Check 5: Beads issue tracking
if ! bd list --status open --json | jq -e '.[] | select(.id == env.CURRENT_ISSUE)' > /dev/null; then
    echo "⚠️  Warning: No open beads issue for this work"
    read -p "Create issue now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bd create "$(git log -1 --pretty=%B)" --priority 2 --type task
    fi
fi

echo "✅ Pre-commit checks passed"
```

**Installation enforcement:**

```bash
# During harness init, install hooks automatically
cat > .harness/install_hooks.sh << 'EOF'
#!/bin/bash

# Copy pre-commit hook
cp .harness/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Copy pre-push hook
cp .harness/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Verify installation
if [ -f .git/hooks/pre-commit ]; then
    echo "✅ Git hooks installed"
else
    echo "❌ Hook installation failed"
    exit 1
fi
EOF
```

### D. Solution 3: CI-Level Validation

**GitHub Actions workflow that validates orchestrator compliance:**

```yaml
# .github/workflows/orchestrator-validation.yml
name: Orchestrator Validation

on:
  pull_request:
    branches: [main, master]
  push:
    branches: [main, master]  # Emergency detection

jobs:
  validate-compliance:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for validation
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install agent-harness
      
      - name: Check for unauthorized direct commits
        if: github.event_name == 'push'
        run: |
          echo "❌ UNAUTHORIZED DIRECT COMMIT TO MAIN DETECTED"
          echo "Commit: ${{ github.sha }}"
          echo "Author: ${{ github.actor }}"
          
          # Revert the commit
          git revert --no-edit ${{ github.sha }}
          git push
          
          # Create incident issue
          bd create "INCIDENT: Unauthorized commit to main by ${{ github.actor }}" \
            --priority 0 \
            --type bug \
            --labels incident,security
          
          # Fail the workflow
          exit 1
      
      - name: Validate PR has orchestrator approval
        if: github.event_name == 'pull_request'
        run: |
          # Check for orchestrator approval marker
          if ! grep -q "ORCHESTRATOR_APPROVED" <<< "${{ github.event.pull_request.body }}"; then
            echo "❌ PR missing orchestrator approval"
            echo "Run orchestrator validation before creating PR"
            exit 1
          fi
      
      - name: Validate beads issue exists
        run: |
          # Extract issue ID from PR title or commit message
          ISSUE_ID=$(echo "${{ github.event.pull_request.title || github.event.head_commit.message }}" | grep -oP 'bd-[a-z0-9]+' | head -1)
          
          if [ -z "$ISSUE_ID" ]; then
            echo "❌ No beads issue referenced"
            exit 1
          fi
          
          # Verify issue exists and is open
          if ! bd show "$ISSUE_ID" --json | jq -e '.status == "open"'; then
            echo "❌ Beads issue $ISSUE_ID not found or not open"
            exit 1
          fi
      
      - name: Run orchestrator compliance check
        run: |
          python check_protocol_compliance.py --validate-pr \
            --pr-number ${{ github.event.pull_request.number }}
      
      - name: Validate test coverage
        run: |
          pytest tests/ --cov=src --cov-report=json
          
          # Check coverage threshold
          COVERAGE=$(jq '.totals.percent_covered' coverage.json)
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "❌ Coverage $COVERAGE% below threshold (80%)"
            exit 1
          fi
```

**Result:** Even if git hooks are bypassed, CI will catch and revert unauthorized commits.

### E. Solution 4: Session Tracking System

**Enforce that all work happens within tracked sessions:**

```python
# agent_harness/session_tracker.py

import json
import os
import time
from pathlib import Path
from typing import Optional

class SessionTracker:
    """Track agent sessions and enforce compliance."""
    
    SESSION_FILE = Path(".harness/session.lock")
    SESSION_LOG = Path(".harness/sessions.jsonl")
    
    def __init__(self):
        self.SESSION_FILE.parent.mkdir(exist_ok=True)
    
    def init_session(self, mode: str, issue_id: str) -> str:
        """Initialize a new session."""
        # Check for existing session
        if self.has_active_session():
            raise Exception(
                "Active session already exists. "
                "Close it first: python check_protocol_compliance.py --close"
            )
        
        # Create session
        session_id = f"session-{int(time.time())}"
        session_data = {
            "id": session_id,
            "mode": mode,
            "issue_id": issue_id,
            "started_at": time.time(),
            "status": "active"
        }
        
        # Write session lock
        self.SESSION_FILE.write_text(json.dumps(session_data))
        
        # Log session start
        with open(self.SESSION_LOG, "a") as f:
            f.write(json.dumps({
                **session_data,
                "event": "session_started"
            }) + "\n")
        
        return session_id
    
    def has_active_session(self) -> bool:
        """Check if active session exists."""
        if not self.SESSION_FILE.exists():
            return False
        
        try:
            session = json.loads(self.SESSION_FILE.read_text())
            
            # Check expiration (8 hours)
            if time.time() - session["started_at"] > 8 * 3600:
                return False
            
            return session["status"] == "active"
        except:
            return False
    
    def get_session(self) -> Optional[dict]:
        """Get current session data."""
        if not self.has_active_session():
            return None
        
        return json.loads(self.SESSION_FILE.read_text())
    
    def validate_session(self, required_mode: Optional[str] = None) -> bool:
        """Validate current session."""
        session = self.get_session()
        
        if not session:
            raise Exception(
                "No active session. Initialize with: "
                "python check_protocol_compliance.py --init"
            )
        
        if required_mode and session["mode"] != required_mode:
            raise Exception(
                f"Session mode is '{session['mode']}' but '{required_mode}' required"
            )
        
        return True
    
    def close_session(self, status: str = "completed"):
        """Close the current session."""
        if not self.has_active_session():
            return
        
        session = self.get_session()
        session["status"] = status
        session["ended_at"] = time.time()
        
        # Log session end
        with open(self.SESSION_LOG, "a") as f:
            f.write(json.dumps({
                **session,
                "event": "session_ended"
            }) + "\n")
        
        # Remove lock
        self.SESSION_FILE.unlink()
    
    def require_session(func):
        """Decorator to require active session."""
        def wrapper(*args, **kwargs):
            tracker = SessionTracker()
            if not tracker.has_active_session():
                raise Exception(
                    "No active harness session. "
                    "Initialize with: python check_protocol_compliance.py --init"
                )
            return func(*args, **kwargs)
        return wrapper
```

**Usage in tools:**

```python
from agent_harness import SessionTracker

@SessionTracker.require_session
def write_file(path: str, content: str):
    """Write file - requires active session."""
    # ... implementation ...

@SessionTracker.require_session
def bash_command(cmd: str):
    """Run bash - requires active session."""
    # ... implementation ...
```

**Result:** Tools **cannot** be used without an active session.

---

## III. Layer 2: Harness Entry Enforcement

### A. Mandatory Initialization Check

**Problem:** Agent can skip `check_protocol_compliance.py --init`

**Solution:** Make initialization a prerequisite for all operations.

```python
# check_protocol_compliance.py

import sys
from agent_harness import SessionTracker, InnerHarness, run_harness

def main():
    tracker = SessionTracker()
    
    if "--init" in sys.argv:
        # Initialize session
        mode = input("Mode (simple/full): ").strip()
        issue_id = input("Beads issue ID: ").strip()
        
        # Validate issue exists
        import subprocess
        result = subprocess.run(
            ["bd", "show", issue_id, "--json"],
            capture_output=True
        )
        if result.returncode != 0:
            print(f"❌ Issue {issue_id} not found")
            sys.exit(1)
        
        session_id = tracker.init_session(mode, issue_id)
        print(f"✅ Session initialized: {session_id}")
        print(f"Mode: {mode}")
        print(f"Tracking: {issue_id}")
        
        # Update beads issue
        subprocess.run([
            "bd", "update", issue_id,
            "--status", "in_progress",
            "--notes", f"Session started: {session_id}"
        ])
        
    elif "--close" in sys.argv:
        # Close session
        session = tracker.get_session()
        if session:
            tracker.close_session()
            
            # Update beads issue
            subprocess.run([
                "bd", "update", session["issue_id"],
                "--status", "open",
                "--notes", "Session ended"
            ])
            
            print("✅ Session closed")
        else:
            print("No active session")
    
    else:
        # Validate session exists
        if not tracker.has_active_session():
            print("❌ No active session")
            print("Initialize first: python check_protocol_compliance.py --init")
            sys.exit(1)
        
        session = tracker.get_session()
        print(f"✅ Active session: {session['id']}")
        print(f"Mode: {session['mode']}")
        print(f"Issue: {session['issue_id']}")

if __name__ == "__main__":
    main()
```

**Enforcement in AGENTS.md:**

```markdown
# CRITICAL: Session Initialization Protocol

Before ANY work, you MUST:

1. Check for active session:
   ```bash
   python check_protocol_compliance.py
   ```

2. If no session, initialize:
   ```bash
   python check_protocol_compliance.py --init
   ```
   - Choose mode: `simple` for quick tasks, `full` for code changes
   - Provide beads issue ID

3. Verify session is active before using ANY tools

4. When done, close session:
   ```bash
   python check_protocol_compliance.py --close
   ```

**VIOLATION:** Using tools without active session will fail.
**ENFORCEMENT:** Git hooks verify session exists before commits.
```

### B. Session Validation in Tool Wrappers

**Wrap all tools with session validation:**

```python
# agent_harness/tools.py

from functools import wraps
from agent_harness import SessionTracker

def require_session(required_mode: str = None):
    """Decorator requiring active session."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracker = SessionTracker()
            
            # Validate session exists
            session = tracker.get_session()
            if not session:
                raise Exception(
                    f"Tool '{func.__name__}' requires active harness session. "
                    "Initialize with: python check_protocol_compliance.py --init"
                )
            
            # Validate mode if specified
            if required_mode and session["mode"] != required_mode:
                raise Exception(
                    f"Tool '{func.__name__}' requires '{required_mode}' mode. "
                    f"Current mode: {session['mode']}"
                )
            
            # Log tool usage
            with open(".harness/tool_usage.log", "a") as f:
                f.write(f"{time.time()},{session['id']},{func.__name__}\n")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example tool implementations

@require_session()
def read_file(path: str) -> str:
    """Read file content."""
    return Path(path).read_text()

@require_session(required_mode="full")
def write_file(path: str, content: str):
    """Write file - requires Full Mode."""
    Path(path).write_text(content)

@require_session(required_mode="full")
def bash_command(cmd: str) -> str:
    """Execute bash - requires Full Mode."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout
```

**Result:** Tools fail immediately if session not initialized.

---

## IV. Layer 3: In-Harness Runtime Enforcement

(This was covered in detail in the previous `agent_harness_hardening.md` document)

**Quick summary:**
- Tool whitelisting
- Approval gate enforcement (via LangGraph interrupts)
- State validation (Pydantic)
- Behavioral monitoring
- Escape attempt detection

---

## V. Hotfix Workflow (Controlled Bypass)

Since agents need a legitimate way to make emergency fixes, provide a **controlled bypass path**:

### A. Hotfix Branch Convention

```bash
# .github/workflows/hotfix-validation.yml
name: Hotfix Fast Track

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize]

jobs:
  validate-hotfix:
    runs-on: ubuntu-latest
    if: startsWith(github.head_ref, 'hotfix/')
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate hotfix criteria
        run: |
          # Check 1: Beads issue with priority 0 or 1
          ISSUE_ID=$(echo "${{ github.event.pull_request.title }}" | grep -oP 'bd-[a-z0-9]+')
          PRIORITY=$(bd show "$ISSUE_ID" --json | jq '.priority')
          
          if [ "$PRIORITY" -gt 1 ]; then
            echo "❌ Hotfixes require priority 0 or 1 (found: $PRIORITY)"
            exit 1
          fi
          
          # Check 2: Small changeset (< 50 lines)
          LINES_CHANGED=$(git diff --stat origin/main | tail -1 | awk '{print $4}')
          if [ "$LINES_CHANGED" -gt 50 ]; then
            echo "❌ Hotfixes limited to 50 lines (found: $LINES_CHANGED)"
            echo "Large changes require full protocol"
            exit 1
          fi
          
          # Check 3: Tests exist and pass
          pytest tests/ -x
      
      - name: Auto-approve if criteria met
        run: |
          gh pr review ${{ github.event.pull_request.number }} --approve
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Auto-merge
        uses: pascalgn/automerge-action@v0.16.2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          MERGE_LABELS: "hotfix"
          MERGE_METHOD: "squash"
```

### B. Emergency Override Protocol

For true emergencies (production down):

```python
# emergency_override.py

import os
import sys
import subprocess
from agent_harness import SessionTracker

def emergency_override():
    """Emergency override for production incidents."""
    
    # Require justification
    print("⚠️  EMERGENCY OVERRIDE PROTOCOL")
    print("This bypasses standard harness checks.")
    print()
    
    incident_id = input("Incident ticket ID (bd-xxxx): ").strip()
    justification = input("Justification: ").strip()
    
    if not incident_id or not justification:
        print("❌ Emergency override requires incident ID and justification")
        sys.exit(1)
    
    # Validate incident exists and is P0
    result = subprocess.run(
        ["bd", "show", incident_id, "--json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Incident {incident_id} not found")
        sys.exit(1)
    
    import json
    issue = json.loads(result.stdout)
    
    if issue["priority"] != 0:
        print(f"❌ Emergency override requires P0 incident (found: P{issue['priority']})")
        sys.exit(1)
    
    # Create emergency session
    tracker = SessionTracker()
    session_id = tracker.init_session(
        mode="emergency",
        issue_id=incident_id
    )
    
    # Log override
    with open(".harness/emergency_overrides.log", "a") as f:
        f.write(json.dumps({
            "timestamp": time.time(),
            "session_id": session_id,
            "incident_id": incident_id,
            "justification": justification,
            "user": os.getenv("USER")
        }) + "\n")
    
    # Update issue
    subprocess.run([
        "bd", "update", incident_id,
        "--status", "in_progress",
        "--notes", f"Emergency override: {justification}"
    ])
    
    print(f"✅ Emergency session: {session_id}")
    print("⚠️  All changes will be audited")
    print(f"Working on: {incident_id}")
    
    return session_id

if __name__ == "__main__":
    emergency_override()
```

**Usage:**

```bash
# Production is down - need immediate fix
python emergency_override.py
# Creates emergency session
# Make fix
# Commit and push (hooks detect emergency mode)
# Post-incident review required within 24h
```

---

## VI. Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT WORKFLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Start                                                           │
│    ↓                                                             │
│  ┌──────────────────────────────────────┐                       │
│  │ Layer 1: Git Protection               │                       │
│  │                                       │                       │
│  │ ✓ Branch protection on main           │                       │
│  │ ✓ Pre-commit hook checks session      │                       │
│  │ ✓ Pre-push hook runs validation       │                       │
│  └──────────────────┬───────────────────┘                       │
│                     ↓                                            │
│  ┌──────────────────────────────────────┐                       │
│  │ Layer 2: Session Management           │                       │
│  │                                       │                       │
│  │ Check: Active session exists?         │                       │
│  │   NO → Run: check_protocol_compliance │                       │
│  │          --init                       │                       │
│  │   YES → Validate mode for task        │                       │
│  └──────────────────┬───────────────────┘                       │
│                     ↓                                            │
│  ┌──────────────────────────────────────┐                       │
│  │ Layer 3: Tool Execution               │                       │
│  │                                       │                       │
│  │ ✓ Session validation on each tool    │                       │
│  │ ✓ Mode validation (simple vs full)   │                       │
│  │ ✓ Tool usage logging                  │                       │
│  └──────────────────┬───────────────────┘                       │
│                     ↓                                            │
│  ┌──────────────────────────────────────┐                       │
│  │ Layer 4: Orchestrator (Full Mode)    │                       │
│  │                                       │                       │
│  │ ✓ Approval gates (LangGraph)          │                       │
│  │ ✓ State validation (Pydantic)         │                       │
│  │ ✓ Behavioral monitoring               │                       │
│  └──────────────────┬───────────────────┘                       │
│                     ↓                                            │
│  ┌──────────────────────────────────────┐                       │
│  │ Commit & Push                         │                       │
│  │                                       │                       │
│  │ ✓ Pre-commit: Session active?         │                       │
│  │ ✓ Pre-push: Full validation           │                       │
│  │ ✓ Create PR (can't push to main)     │                       │
│  └──────────────────┬───────────────────┘                       │
│                     ↓                                            │
│  ┌──────────────────────────────────────┐                       │
│  │ CI Validation                         │                       │
│  │                                       │                       │
│  │ ✓ Orchestrator approval in PR        │                       │
│  │ ✓ Beads issue exists and open        │                       │
│  │ ✓ Tests pass                          │                       │
│  │ ✓ Coverage meets threshold            │                       │
│  └──────────────────┬───────────────────┘                       │
│                     ↓                                            │
│  Merge (if approved)                                             │
│                                                                  │
│  ═══════════════════════════════════════                        │
│                                                                  │
│  EMERGENCY PATH (P0 incidents only):                            │
│                                                                  │
│  python emergency_override.py                                   │
│    ↓                                                             │
│  Create hotfix/bd-xxxx branch                                   │
│    ↓                                                             │
│  Make minimal fix (<50 lines)                                   │
│    ↓                                                             │
│  Push → Fast-track PR → Auto-merge                              │
│    ↓                                                             │
│  Post-incident review (required)                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## VII. Implementation Checklist

### Phase 1: Critical Fixes (Do First)

- [ ] **Enable GitHub branch protection on `main`**
  - Block direct pushes
  - Require PR reviews
  - Require status checks
  - Enforce for admins

- [ ] **Install git hooks**
  - Pre-commit: Check active session
  - Pre-commit: Prevent commits to `main`
  - Pre-push: Run full validation

- [ ] **Implement session tracking**
  - Create SessionTracker class
  - Add session lock file
  - Add session logging

### Phase 2: Enforcement Layer (Week 1)

- [ ] **Wrap tools with session validation**
  - Add `@require_session` decorator
  - Update all tool implementations
  - Add mode validation (simple/full)

- [ ] **Create CI validation workflow**
  - Orchestrator approval check
  - Beads issue validation
  - Test coverage enforcement

- [ ] **Add session management CLI**
  - `--init` for session start
  - `--close` for session end
  - `--status` for session info

### Phase 3: Hotfix Support (Week 2)

- [ ] **Create hotfix workflow**
  - Fast-track PR validation
  - Auto-merge for small changes
  - P0/P1 priority requirement

- [ ] **Implement emergency override**
  - Incident validation
  - Justification logging
  - Post-incident review tracking

- [ ] **Document hotfix process**
  - Update AGENTS.md
  - Create runbook
  - Train team

### Phase 4: Monitoring & Auditing (Ongoing)

- [ ] **Session audit logging**
  - Track all sessions
  - Log tool usage
  - Monitor emergency overrides

- [ ] **Compliance reporting**
  - Weekly session summary
  - Emergency override review
  - Violation detection

---

## VIII. Comparison: Before vs After

### Before (Voluntary Compliance)

```
Agent wants to make change
  ↓
Agent decides: Use harness? (Optional)
  ↓ YES → Enters harness → Protected
  ↓ NO  → Direct commit → BYPASS ⚠️
```

**Result:** Agent bypassed by committing directly to `main`.

### After (Enforced Compliance)

```
Agent wants to make change
  ↓
Git hook: Active session? (Mandatory)
  ↓ NO → ERROR: Initialize session first
  ↓ YES → Continue
  ↓
Tool: Session valid? (Mandatory)
  ↓ NO → ERROR: Invalid session
  ↓ YES → Execute
  ↓
Git push to main? (Blocked)
  ↓ ERROR: Create PR instead
  ↓
PR → CI validation (Mandatory)
  ↓ FAIL → Rejection
  ↓ PASS → Approval
```

**Result:** Agent **cannot** bypass enforcement layers.

---

## IX. Agent's Suggestions Analysis

The agent suggested:

1. **Git branch protection** ✅ Addressed in Layer 1B
2. **CI-level enforcement** ✅ Addressed in Layer 1D
3. **Pre-commit hooks** ✅ Addressed in Layer 1C
4. **Hotfix branches** ✅ Addressed in Section V
5. **Emergency flags** ✅ Addressed in Section VB

**Additional improvements beyond agent's suggestions:**

6. **Session tracking system** (new)
7. **Tool-level validation** (new)
8. **Mode enforcement** (simple vs full) (new)
9. **Audit logging** (new)
10. **Multi-layer architecture** (new)

---

## X. Testing the Enforcement

### Test 1: Direct Commit to Main

```bash
# Should fail at pre-commit hook
git checkout main
echo "test" > test.txt
git add test.txt
git commit -m "Direct commit"
# Expected: ❌ Direct commits to main are not allowed
```

### Test 2: No Active Session

```bash
# Should fail at pre-commit hook
git checkout -b feature/test
echo "test" > test.txt
git add test.txt
git commit -m "Test"
# Expected: ❌ Orchestrator not initialized for this session
```

### Test 3: Tool Without Session

```python
# Should fail immediately
from agent_harness.tools import write_file

write_file("test.txt", "content")
# Expected: Exception: Tool 'write_file' requires active harness session
```

### Test 4: Emergency Override (Valid)

```bash
# Should succeed with P0 incident
bd create "P0: Production down" --priority 0
python emergency_override.py
# Provide incident ID
# Make fix
git commit -m "Emergency fix"
# Expected: ✅ Allowed (logged for review)
```

### Test 5: CI Rejects Unauthorized Commit

```bash
# Somehow bypass hooks and push to main
git push origin main --force --no-verify
# Expected: CI detects, reverts, creates incident issue
```

---

## Summary

**Root cause:** Voluntary compliance is not enforcement.

**The fix:**

1. **Layer 1 (Git):** Branch protection + hooks prevent direct commits
2. **Layer 2 (Session):** Tracked sessions make harness mandatory
3. **Layer 3 (Tools):** Tools fail without valid session
4. **Layer 4 (Runtime):** In-harness protections (previous document)
5. **Emergency path:** Controlled hotfix workflow for P0 incidents

**Key insight:** The agent was right - you need **architectural enforcement**, not just instructions. The harness must be **unavoidable**, not optional.

**Implementation priority:**
1. Git branch protection (5 min)
2. Pre-commit hook (15 min)
3. Session tracking (2 hours)
4. Tool validation (3 hours)
5. CI validation (2 hours)

**Total setup time:** ~8 hours for complete enforcement architecture.

**Result:** Agents **cannot** bypass harness without triggering alarms and automatic reversion.
