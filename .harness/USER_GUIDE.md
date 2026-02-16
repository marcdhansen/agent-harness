# Cleanup Enforcement System - User Guide

## Overview

The cleanup enforcement system prevents temporary files from polluting the repository through multi-layer validation.

## Quick Start

### Installation
```bash
# Install git hooks
bash .harness/install_hooks.sh

# Verify installation
bash .harness/scripts/status-dashboard.sh
```

### Daily Workflow
```bash
# 1. Start session
python check_protocol_compliance.py --init
# Choose: simple or full mode
# Provide: beads issue ID

# 2. Work on task
# ... make changes ...

# 3. Check status anytime
python check_protocol_compliance.py --status

# 4. Before committing
bash .harness/scripts/validate-cleanup.sh

# 5. Commit (hook validates automatically)
git commit -m "your message"

# 6. Before creating PR
bash .harness/scripts/pre-pr-checklist.sh

# 7. Close session
python check_protocol_compliance.py --close
```

## Enforcement Layers

### Layer 1: Pre-commit Hook (Medium)
- **When:** Before each commit
- **What:** Validates no temp files staged
- **Action:** Warns, asks confirmation
- **Bypass:** `git commit --no-verify` (not recommended)

### Layer 2: Session Cleanup (Hard)
- **When:** Session close
- **What:** Validates workspace clean
- **Action:** Blocks until clean
- **Bypass:** `--skip-validation` flag (emergency only)

### Layer 3: CI Validation (Hard)
- **When:** On PR creation
- **What:** Scans all PR files
- **Action:** Blocks merge
- **Bypass:** None

### Layer 4: Worktree Validation (Hard)
- **When:** Worktree removal, session close
- **What:** Checks for uncommitted changes, temp files
- **Action:** Blocks removal
- **Bypass:** `validate_cleanup=False` (code only)

## Common Scenarios

### Scenario 1: "I have temp files and want to commit"
```bash
# Option 1: Remove them (recommended)
bash .harness/scripts/auto-cleanup.sh

# Option 2: Review and remove manually
bash .harness/scripts/validate-cleanup.sh
rm <file>

# Option 3: Override pre-commit (NOT recommended)
git commit --no-verify
# Note: CI will still block PR
```

### Scenario 2: "Can't close session due to violations"
```bash
# Check what's wrong
python check_protocol_compliance.py --status

# Fix violations
bash .harness/scripts/auto-cleanup.sh

# Try again
python check_protocol_compliance.py --close

# Emergency override (logs for audit)
python check_protocol_compliance.py --close --skip-validation
```

### Scenario 3: "PR blocked by CI"
```bash
# See what CI found
# (Check PR comments for violation list)

# Fix locally
bash .harness/scripts/auto-cleanup.sh

# Commit and push
git add -u
git commit -m "chore: remove temporary files"
git push

# CI will re-run and pass
```

### Scenario 4: "Orphaned worktrees"
```bash
# Check for orphans
git worktree list

# Clean up
bash .harness/scripts/cleanup-worktrees.sh

# Or manually
git worktree remove <path> --force
```

## Utility Scripts

### validate-cleanup.sh
Quick validation without full compliance check.
```bash
bash .harness/scripts/validate-cleanup.sh
```

### auto-cleanup.sh
Automatically remove all violations.
```bash
bash .harness/scripts/auto-cleanup.sh
# Prompts for confirmation
```

### pre-pr-checklist.sh
Comprehensive pre-PR validation.
```bash
bash .harness/scripts/pre-pr-checklist.sh
# Checks: cleanup, session, git status, worktrees, tests
```

### status-dashboard.sh
Shows system status and current workspace state.
```bash
bash .harness/scripts/status-dashboard.sh
```

### cleanup-worktrees.sh
Manage git worktrees.
```bash
bash .harness/scripts/cleanup-worktrees.sh
```

## Pattern Configuration

Patterns are defined in `.harness/cleanup_patterns.txt`.

### Adding Patterns
```bash
# Edit patterns file
echo "*.log" >> .harness/cleanup_patterns.txt

# Patterns support:
# - Glob patterns: *.tmp, debug_*
# - Comments: # This is a comment
# - Empty lines: (ignored)
```

### Pattern Categories
```
# Temporary files
*.tmp
*.temp
*.bak

# Debug artifacts
debug_*
*_scratch.*

# Database runtime
*_state*.db
harness_*.db

# Session artifacts
.harness/session_*.lock
```

## Troubleshooting

### Issue: Hook not running
```bash
# Verify hook exists
ls -l .git/hooks/pre-commit

# Reinstall
bash .harness/install_hooks.sh

# Test manually
bash .git/hooks/pre-commit
```

### Issue: False positive (legitimate file)
```bash
# Option 1: Rename file
mv myfile.tmp myfile.data

# Option 2: Remove pattern
# Edit .harness/cleanup_patterns.txt
# Remove or comment out the pattern

# Option 3: Override (last resort)
git commit --no-verify
```

### Issue: CI fails but local passes
```bash
# CI uses same patterns
# Likely cause: pattern interpretation difference

# Simulate CI locally
bash .harness/scripts/validate-cleanup.sh

# Or check PR comments for specific files
```

## Best Practices

1. **Run validation before committing**
   ```bash
   bash .harness/scripts/validate-cleanup.sh
   ```

2. **Close sessions when done**
   ```bash
   python check_protocol_compliance.py --close
   ```

3. **Use auto-cleanup for bulk removal**
   ```bash
   bash .harness/scripts/auto-cleanup.sh
   ```

4. **Check dashboard periodically**
   ```bash
   bash .harness/scripts/status-dashboard.sh
   ```

5. **Don't bypass enforcement** unless absolutely necessary

## Emergency Procedures

### Production Hotfix

If you need to bypass for emergency:
```bash
# 1. Make minimal fix
# 2. Use --no-verify
git commit --no-verify -m "hotfix: critical fix"

# 3. Push directly (if authorized)
git push --no-verify

# 4. Clean up after
bash .harness/scripts/auto-cleanup.sh
git commit -m "chore: cleanup after hotfix"
git push

# 5. Document in post-incident review
```

### Stuck Session

If session won't close:
```bash
# Force close (logs for audit)
python check_protocol_compliance.py --close --skip-validation

# Or manually remove lock
rm .agent/sessions/session.lock

# Then clean up
bash .harness/scripts/auto-cleanup.sh
```

## FAQ

**Q: Why can't I commit my .tmp file?**  
A: Temporary files shouldn't be version controlled. Use .gitignore or rename.

**Q: Can I disable enforcement?**  
A: Not recommended. For emergencies, use bypass flags.

**Q: Does this slow down my workflow?**  
A: Minimal impact - validation is fast (<1 second).

**Q: What if I'm working on cleanup tools?**  
A: Use a different file extension or exclude pattern.

**Q: How do I add custom patterns?**  
A: Edit `.harness/cleanup_patterns.txt`.

## Getting Help

- **Check dashboard:** `bash .harness/scripts/status-dashboard.sh`
- **Validation:** `bash .harness/scripts/validate-cleanup.sh`
- **Documentation:** This guide + README.md
- **Team:** Ask in #agent-harness channel
