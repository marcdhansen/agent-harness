# Orchestrator Skill - Fallback Mechanisms Enhancement

## Purpose

Add fallback validation mechanisms to prevent total system failure if Python scripts are unavailable.

## Integration

Add this section after the "Usage" section in Orchestrator/SKILL.md:

---

## 🛡️ Fallback Validation Mode

### When to Use Fallback Mode

Fallback mode activates when:
- Python script `check_protocol_compliance.py` fails to execute
- Python environment is broken or misconfigured
- Script file is missing or corrupted
- Emergency bypass needed

### Manual Initialization Checklist

If automatic checks fail, use manual validation:

```bash
# 1. Verify required tools exist
which bd git uv python
# Expected: All commands found

# 2. Check planning documents exist
ls ImplementationPlan.md WorkingMemory.md
# Expected: Both files present

# 3. Verify git repository is clean
git status --porcelain | wc -l
# Expected: 0 (no uncommitted changes)

# 4. Check beads issue assigned
cat .beads/current
# Expected: Issue ID present (e.g., "TASK-123")

# 5. Verify plan approval (if required)
grep -A 5 "## Approval" ImplementationPlan.md
# Expected: Approval timestamp within expiry window
```

### Manual Finalization Checklist

If automatic checks fail, use manual validation:

```bash
# 1. Verify all work committed
git status
# Expected: "nothing to commit, working tree clean"

# 2. Check quality gates passed (if applicable)
pytest && ruff check . && mypy .
# Expected: All pass

# 3. Verify issue status updated
bd list --status in-progress
# Expected: Your current issue

# 4. Check reflection captured
ls .agent/reflections/
# Expected: Recent reflection file

# 5. Confirm all changes pushed
git fetch origin && git diff origin/$(git branch --show-current)
# Expected: No differences
```

### Fallback Status Output Format

When using fallback mode, provide clear status:

```
⚠️ FALLBACK MODE - Script Unavailable

INITIALIZATION STATUS (Manual Validation):
├── Tools: ✅ All required tools available (verified)
├── Context: ✅ Planning documents present (verified)
├── Git: ✅ Repository clean (verified)
└── Issues: ✅ Issue TASK-123 assigned (verified)

Status: READY TO PROCEED (manual validation)

Note: Automatic validation unavailable. Manual checks completed.
```

### Graceful Degradation Strategy

```bash
# Priority 1: Try automatic validation
if command -v python3 >/dev/null 2>&1; then
    python3 ~/.gemini/antigravity/skills/Orchestrator/scripts/check_protocol_compliance.py --init
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Automatic validation passed"
        exit 0
    fi
fi

# Priority 2: Try fallback validation
echo "⚠️ Automatic validation unavailable, using fallback"
echo ""
echo "Manual Validation Checklist:"
echo "1. Tools available?"
which bd git uv || echo "❌ Missing tools"

echo "2. Planning documents present?"
ls ImplementationPlan.md WorkingMemory.md || echo "❌ Missing documents"

echo "3. Git clean?"
[ "$(git status --porcelain | wc -l)" -eq 0 ] && echo "✅ Clean" || echo "❌ Uncommitted changes"

echo "4. Issue assigned?"
[ -f .beads/current ] && echo "✅ $(cat .beads/current)" || echo "❌ No issue"

# Priority 3: Emergency bypass (user approval required)
echo ""
echo "⚠️ EMERGENCY BYPASS available with user approval"
echo "Type 'bypass' to proceed without validation (not recommended):"
read -r response
if [ "$response" = "bypass" ]; then
    echo "🚨 PROCEEDING WITHOUT VALIDATION"
fi
```

### Configuration

Add to orchestrator.yaml:

```yaml
fallback:
  enabled: true
  manual_checks_required: true
  emergency_bypass_allowed: false  # Require explicit user approval
  
  manual_validation:
    tools_check: true
    git_check: true
    documents_check: true
    beads_check: true
```

## Benefits

1. **System Resilience**: Orchestrator never completely fails
2. **Clear Feedback**: Manual checklists guide user through validation
3. **Emergency Access**: Can still proceed in critical situations
4. **Audit Trail**: Manual validations are logged

## Testing

```bash
# Test fallback mode
# 1. Rename Python script temporarily
mv check_protocol_compliance.py check_protocol_compliance.py.bak

# 2. Run orchestrator (should enter fallback mode)
/orchestrator --init

# 3. Verify manual checklist displayed
# 4. Complete manual validation
# 5. Restore script
mv check_protocol_compliance.py.bak check_protocol_compliance.py
```

## Integration Points

- **Initialization Process**: Fallback mode during initialization
- **Finalization Process**: Fallback mode during finalization
- **Error Handling**: Graceful degradation on script failure
- **Logging**: All fallback usage logged for analysis
