# Orchestrator Skill - Flexible Approval Policy Enhancement

## Purpose

Replace rigid 4-hour approval expiry with context-aware, flexible approval times based on task complexity and type.

## Integration

Replace the `plan_approval_hours: 4` section in orchestrator.yaml with this enhanced configuration:

---

## ⏰ Context-Aware Approval Policy

### Task-Based Expiry Times

Different tasks require different time windows:

```yaml
approval_policy:
  # Task type → Approval duration (hours)
  task_types:
    quick_fix: 2          # Bug fixes, typos, small changes
    standard: 6           # Normal features, refactors
    complex: 12           # Architecture changes, large features
    research: 24          # Spikes, exploration, investigation
    debugging: 48         # Long-running debugging sessions
  
  # Default if task type not specified
  default: 6
  
  # Enforcement strategy (hours → action)
  enforcement:
    soft_warning: 8       # Show warning, don't block
    soft_block: 24        # Require justification
    hard_block: 72        # Must re-approve or create new plan
```

### Auto-Extension Triggers

Plans automatically extend when:

```yaml
auto_extension:
  enabled: true
  
  triggers:
    progress_threshold: 0.5  # >50% tasks complete
    significant_commit: true  # Meaningful commits made
    user_confirmation: true   # User confirms plan still valid
  
  extension_duration: 6  # Hours to extend by
  max_extensions: 3      # Maximum auto-extensions
```

### Graduated Enforcement

```bash
# < 8 hours: No action
if [ $hours_elapsed -lt 8 ]; then
    echo "✅ Plan approval valid"
    exit 0
fi

# 8-24 hours: Warning only
if [ $hours_elapsed -lt 24 ]; then
    echo "⚠️ Plan approval aging (${hours_elapsed}h)"
    echo "Consider reviewing plan or requesting extension"
    exit 0  # Don't block
fi

# 24-72 hours: Soft block (justification required)
if [ $hours_elapsed -lt 72 ]; then
    echo "🔶 Plan approval expired (${hours_elapsed}h)"
    echo ""
    echo "Options:"
    echo "1. Justify continuation (debugging, investigation, etc.)"
    echo "2. Request plan extension (bd extend-approval)"
    echo "3. Re-approve plan"
    echo ""
    read -p "Enter option [1-3]: " choice
    
    if [ "$choice" = "1" ]; then
        read -p "Justification: " justification
        echo "Continuing with justification: $justification"
        exit 0
    fi
    
    exit 1  # Block until action taken
fi

# > 72 hours: Hard block
echo "❌ Plan approval hard-expired (${hours_elapsed}h)"
echo "Must either:"
echo "1. Re-approve existing plan (bd approve-plan)"
echo "2. Create new plan (bd create-plan)"
exit 1
```

### Task Type Detection

```bash
# Detect task type from issue labels or description

detect_task_type() {
    local issue_id=$1
    
    # Check beads labels
    labels=$(bd show "$issue_id" --format json | jq -r '.labels[]')
    
    if echo "$labels" | grep -q "quick-fix\|hotfix\|typo"; then
        echo "quick_fix"
    elif echo "$labels" | grep -q "research\|spike\|investigation"; then
        echo "research"
    elif echo "$labels" | grep -q "debug\|bug-hunt"; then
        echo "debugging"
    elif echo "$labels" | grep -q "complex\|architecture\|refactor-large"; then
        echo "complex"
    else
        echo "standard"
    fi
}

# Get appropriate approval duration
task_type=$(detect_task_type "$ISSUE_ID")
approval_hours=$(get_approval_duration "$task_type")

echo "Task type: $task_type"
echo "Approval valid for: ${approval_hours} hours"
```

### Extension Commands

Add to beads CLI (`bd` command):

```bash
# Request plan extension
bd extend-approval --reason "Still debugging memory leak"

# Confirm plan still valid
bd confirm-plan

# Check approval status
bd approval-status

# Example output:
# Plan Approval Status:
# - Created: 2026-02-13 10:00:00
# - Expires: 2026-02-13 22:00:00 (12 hours)
# - Elapsed: 8 hours
# - Status: ⚠️ Warning (approaching expiry)
# - Auto-extensions: 1/3 used
```

### Configuration Examples

```yaml
# Example 1: Quick bug fix
task:
  type: quick_fix
  approval_duration: 2h
  enforcement: soft_warning_only

# Example 2: Complex refactor
task:
  type: complex
  approval_duration: 12h
  auto_extension:
    enabled: true
    triggers: [progress_threshold, significant_commit]

# Example 3: Research spike
task:
  type: research
  approval_duration: 24h
  enforcement: soft_block_only  # Allow continuation with justification
```

## Enhanced Status Display

```bash
# Old (rigid):
✅ Plan approval valid (2.5h elapsed, expires in 1.5h)

# New (flexible):
✅ Plan approval valid
├── Task type: standard
├── Approval duration: 6 hours
├── Elapsed: 2.5 hours (41%)
├── Expires: 2026-02-13 16:00:00
├── Status: Active
└── Auto-extensions: 0/3 available

# With warning:
⚠️ Plan approval aging
├── Task type: debugging
├── Approval duration: 48 hours
├── Elapsed: 32 hours (67%)
├── Expires: 2026-02-15 10:00:00
├── Status: Warning - approaching expiry
├── Auto-extensions: 2/3 used
└── Recommendation: Consider requesting extension
```

## Benefits

1. **Context-Aware**: Different tasks get appropriate time windows
2. **Flexible**: Auto-extension for productive work
3. **Gradual**: Warning → Soft block → Hard block
4. **Transparent**: Clear status and remaining time
5. **Developer-Friendly**: Less bureaucratic overhead

## Migration

For existing deployments:

```bash
# Migrate from old config to new config
python scripts/migrate_approval_policy.py

# Review migration results
cat config/orchestrator.yaml

# Test new policy
/orchestrator --init --dry-run
```

## Testing

```bash
# Test quick fix (2h limit)
bd create-task --type quick-fix "Fix typo in README"
# ... work for 3 hours ...
/orchestrator --finalize  # Should warn but not block

# Test standard task (6h limit)
bd create-task --type standard "Add user authentication"
# ... work for 8 hours ...
/orchestrator --finalize  # Should warn but not block

# Test auto-extension
bd create-task --type complex "Refactor database layer"
# ... work for 10 hours with 60% progress ...
/orchestrator --finalize  # Should auto-extend

# Test hard expiry
bd create-task --type standard "Add caching"
# ... work for 80 hours ...
/orchestrator --finalize  # Should hard block
```

## Backward Compatibility

For existing plans without task type:

```yaml
legacy_handling:
  default_type: standard
  default_duration: 6h
  migration_period: 30d  # Grace period for old plans
```
