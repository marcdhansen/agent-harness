# Orchestrator Skill - Smart Escalation Criteria Enhancement

## Purpose

Refine code change detection to avoid unnecessary escalations from Turbo to Full SOP mode. Distinguish between trivial changes and substantive code modifications.

## Integration

Add this section to Orchestrator/SKILL.md after the "Turbo Mode" section:

---

## 🎯 Smart Escalation Criteria

### Problem with Broad Detection

Current behavior:
- **Any** code file change triggers Full SOP
- Comment changes require heavyweight process
- Typo fixes need full planning
- Test additions escalate unnecessarily

### Enhanced Detection

#### Stay in Turbo Mode For:

```bash
# 1. Comment-only changes
git diff --cached | grep -E '^\+.*#' && ! git diff --cached | grep -E '^\+[^#]*[a-zA-Z]'

# 2. Documentation updates
git diff --cached --name-only | grep -E '\.(md|txt|rst)$'

# 3. Test file additions (no production code modified)
git diff --cached --name-only | grep -E '^tests?/' && \
! git diff --cached --name-only | grep -Ev '^tests?/'

# 4. Formatting/style changes only
git diff --cached | python3 -c "
import sys
lines = sys.stdin.readlines()
# Check if only whitespace changes
logic_changes = [l for l in lines if l.startswith(('+', '-')) and l.strip() not in ['+', '-']]
if not logic_changes:
    sys.exit(0)  # No logic changes
sys.exit(1)
"

# 5. Configuration tweaks
git diff --cached --name-only | grep -E '\.(yaml|yml|json|toml|ini|cfg)$'

# 6. Single-line bug fixes (<5 lines changed)
[ $(git diff --cached --shortstat | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+') -lt 5 ]

# 7. Dependency updates
git diff --cached --name-only | grep -E 'requirements\.txt|pyproject\.toml|package\.json'
```

#### Escalate to Full SOP For:

```bash
# 1. New functions or classes
git diff --cached | grep -E '^\+\s*(def |class |async def )'

# 2. Logic changes in production code
git diff --cached --name-only | grep -Ev '^(tests?/|docs?/)' | \
    xargs -I {} git diff --cached {} | grep -E '^\+[^+]'

# 3. API signature changes
git diff --cached | grep -E '^\+.*def.*\(.*\).*:'

# 4. Database schema modifications
git diff --cached --name-only | grep -E 'migrations?/|schema\.py|models\.py'

# 5. Multi-file refactors (>3 files)
[ $(git diff --cached --name-only | wc -l) -gt 3 ]

# 6. Architecture changes
git diff --cached --name-only | grep -E 'architecture|core/|base\.py'

# 7. Security-critical code
git diff --cached --name-only | grep -E 'auth|security|crypto|password'
```

### Implementation

```bash
#!/bin/bash
# scripts/smart_escalation_check.sh

# Check if we should escalate from Turbo to Full SOP

check_stay_in_turbo() {
    # Returns 0 (true) if should stay in Turbo
    # Returns 1 (false) if should escalate
    
    local changed_files=$(git diff --cached --name-only)
    
    # Empty change? Stay in Turbo
    if [ -z "$changed_files" ]; then
        return 0
    fi
    
    # Only documentation? Stay in Turbo
    if echo "$changed_files" | grep -qE '\.(md|txt|rst)$' && \
       ! echo "$changed_files" | grep -vqE '\.(md|txt|rst)$'; then
        echo "✓ Documentation-only changes (Turbo OK)"
        return 0
    fi
    
    # Only test files? Stay in Turbo
    if echo "$changed_files" | grep -qE '^tests?/' && \
       ! echo "$changed_files" | grep -vqE '^tests?/'; then
        echo "✓ Test-only changes (Turbo OK)"
        return 0
    fi
    
    # Only config files? Stay in Turbo
    if echo "$changed_files" | grep -qE '\.(yaml|yml|json|toml|ini)$' && \
       ! echo "$changed_files" | grep -vqE '\.(yaml|yml|json|toml|ini)$'; then
        echo "✓ Configuration-only changes (Turbo OK)"
        return 0
    fi
    
    # Check for new functions/classes (major change)
    if git diff --cached | grep -qE '^\+\s*(def |class |async def )'; then
        echo "⚠ New functions/classes detected (Escalate to Full SOP)"
        return 1
    fi
    
    # Check for API signature changes
    if git diff --cached | grep -qE '^\+.*def.*\(.*\):' && \
       git diff --cached | grep -qE '^\-.*def.*\(.*\):'; then
        echo "⚠ API signature changes detected (Escalate to Full SOP)"
        return 1
    fi
    
    # Check for multi-file changes (>3 production files)
    local prod_files=$(echo "$changed_files" | grep -Ev '^(tests?/|docs?/)' | wc -l)
    if [ $prod_files -gt 3 ]; then
        echo "⚠ Multi-file changes detected: $prod_files files (Escalate to Full SOP)"
        return 1
    fi
    
    # Check for small changes (<5 lines in production code)
    local insertions=$(git diff --cached --shortstat | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo 0)
    local deletions=$(git diff --cached --shortstat | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo 0)
    local total_changes=$((insertions + deletions))
    
    if [ $total_changes -lt 5 ]; then
        echo "✓ Small changes detected: $total_changes lines (Turbo OK)"
        return 0
    fi
    
    # Default: escalate if unsure
    echo "⚠ Substantive code changes detected (Escalate to Full SOP)"
    return 1
}

# Main check
if check_stay_in_turbo; then
    echo "Decision: STAY IN TURBO MODE"
    exit 0
else
    echo "Decision: ESCALATE TO FULL SOP"
    exit 1
fi
```

### Configuration

Add to orchestrator.yaml:

```yaml
turbo_mode:
  escalation:
    # File patterns that stay in Turbo
    turbo_safe_patterns:
      - "*.md"
      - "*.txt"
      - "*.rst"
      - "tests/**"
      - "*.yaml"
      - "*.yml"
      - "*.json"
      - "*.toml"
      - "requirements.txt"
    
    # File patterns that force Full SOP
    full_sop_patterns:
      - "*/migrations/*"
      - "*/models.py"
      - "*/schema.py"
      - "*/auth/*"
      - "*/security/*"
      - "core/*.py"
    
    # Change thresholds
    thresholds:
      max_turbo_files: 3          # >3 files → Full SOP
      max_turbo_lines: 5          # >5 lines → check deeper
      max_turbo_functions: 0      # Any new function → Full SOP
    
    # Logic change detection
    detect_logic_changes: true
    detect_api_changes: true
    detect_schema_changes: true
```

### Enhanced Status Messages

```bash
# Old (broad):
⚠️ Code changes detected. Escalating to Full SOP.

# New (specific):
✓ TURBO MODE: Comment-only changes (3 lines)
✓ TURBO MODE: Test file additions (no production code)
✓ TURBO MODE: Configuration tweak (config.yaml)
⚠️ ESCALATE: New function added (requires planning)
⚠️ ESCALATE: Multi-file refactor (7 files changed)
⚠️ ESCALATE: API signature changed (breaking change)
```

### Visual Feedback

```bash
# Turbo-safe changes:
git diff --cached --stat
# test_parser.py    | 10 ++++++++++
# README.md         |  2 +-
# 2 files changed, 11 insertions(+), 1 deletion(-)

/orchestrator --check-escalation
# ✓ TURBO MODE APPROVED
# ├── Test additions: OK (no production code)
# ├── Documentation: OK (minor edits)
# ├── New functions: None
# ├── Logic changes: None
# └── Decision: Continue in Turbo Mode

# Escalation-required changes:
git diff --cached --stat
# src/parser.py     | 45 ++++++++++++++++++++++++-----
# src/validator.py  | 23 ++++++++++++---
# src/core.py       | 12 +++++---
# 3 files changed, 70 insertions(+), 10 deletions(-)

/orchestrator --check-escalation
# ⚠️ ESCALATION REQUIRED
# ├── Production files: 3 (threshold: 3)
# ├── New functions: 2 detected
# ├── Logic changes: Substantial
# ├── Lines changed: 70 (threshold: 5)
# └── Decision: Escalate to Full SOP
#
# Please run: /orchestrator --init
```

### Edge Cases

```bash
# Case 1: Comment changes with one-line logic change
git diff --cached
# -    # Old comment
# +    # New comment
# +    if validate:  # One-line logic change

Decision: ESCALATE (logic change present)

# Case 2: Massive comment additions, no code change
git diff --cached
# +    # This is a very long docstring
# +    # explaining what this function does
# +    # ... 50 more lines of comments ...

Decision: STAY IN TURBO (comments only)

# Case 3: Test file + tiny production fix
git diff --cached --name-only
# tests/test_parser.py
# src/parser.py  # 2-line typo fix

Decision: STAY IN TURBO (small fix + tests)

# Case 4: Configuration + schema change
git diff --cached --name-only
# config.yaml
# migrations/0042_add_user_field.py

Decision: ESCALATE (schema change)
```

## Benefits

1. **Reduced Bureaucracy**: Trivial changes don't trigger heavyweight process
2. **Focused Planning**: Full SOP reserved for substantial changes
3. **Clear Criteria**: Developers know what triggers escalation
4. **Faster Iteration**: Quick fixes stay quick
5. **Safety Preserved**: Important changes still get full review

## Testing

```bash
# Test 1: Comment-only change
echo "# New comment" >> src/file.py
git add src/file.py
/orchestrator --check-escalation
# Expected: STAY IN TURBO

# Test 2: New function
echo "def new_function(): pass" >> src/file.py
git add src/file.py
/orchestrator --check-escalation
# Expected: ESCALATE

# Test 3: Test-only
echo "def test_new(): pass" >> tests/test_file.py
git add tests/test_file.py
/orchestrator --check-escalation
# Expected: STAY IN TURBO

# Test 4: Multi-file change
touch src/{a,b,c,d}.py
git add src/*.py
/orchestrator --check-escalation
# Expected: ESCALATE (>3 files)
```

## Migration

Existing Turbo sessions are unaffected. New smart detection applies to:
- Future Turbo sessions
- Existing Turbo sessions on next change
- All escalation checks going forward

No configuration migration required - smart detection is backward compatible.
