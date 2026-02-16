# Cleanup Enforcement - Troubleshooting Guide

## Quick Diagnostics
```bash
# Run comprehensive status check
bash .harness/scripts/status-dashboard.sh

# Check for violations
bash .harness/scripts/validate-cleanup.sh

# Verify hooks installed
ls -l .git/hooks/pre-commit
```

## Common Issues

### 1. "Pre-commit hook not running"

**Symptoms:**
- Commits succeed without validation
- No prompts about temp files

**Diagnosis:**
```bash
ls -l .git/hooks/pre-commit
# Should show executable file
```

**Solutions:**
```bash
# Solution 1: Reinstall hooks
bash .harness/install_hooks.sh

# Solution 2: Make executable
chmod +x .git/hooks/pre-commit

# Solution 3: Check hook content
cat .git/hooks/pre-commit
# Should reference cleanup validation
```

---

### 2. "Session won't close (violations)"

**Symptoms:**
```
❌ Cannot close session:
Session cleanup incomplete:
  - debug.tmp
  - test_scratch.py
```

**Diagnosis:**
```bash
python check_protocol_compliance.py --status
```

**Solutions:**
```bash
# Solution 1: Auto cleanup (recommended)
bash .harness/scripts/auto-cleanup.sh
python check_protocol_compliance.py --close

# Solution 2: Manual cleanup
rm debug.tmp test_scratch.py
python check_protocol_compliance.py --close

# Solution 3: Emergency override
python check_protocol_compliance.py --close --skip-validation
# Note: Logs for audit
```

---

### 3. "CI blocking PR merge"

**Symptoms:**
- PR has ❌ red X on "Cleanup Validation"
- Bot comment lists violations

**Diagnosis:**
- Check PR comments for file list
- Run locally: `bash .harness/scripts/validate-cleanup.sh`

**Solutions:**
```bash
# Solution 1: Auto cleanup and push
bash .harness/scripts/auto-cleanup.sh
git add -u
git commit -m "chore: remove temporary files"
git push

# Solution 2: Manual review and fix
# Read PR comment, remove specific files
rm <files from PR comment>
git add -u
git commit -m "chore: cleanup"
git push

# CI will re-run automatically
```

---

### 4. "False positive (legitimate file)"

**Symptoms:**
- Legitimate file flagged as violation
- File matches pattern but should be committed

**Examples:**
- `src/temp_table_handler.py` (production code, not temp file)
- `tests/fixtures/temp_data.json` (test fixture)

**Solutions:**
```bash
# Solution 1: Rename file (recommended)
mv temp_table_handler.py table_handler.py

# Solution 2: Add exception to patterns
# Edit .harness/cleanup_patterns.txt

# Solution 3: Use .gitignore
echo "myfile.tmp" >> .gitignore

# Solution 4: Override (last resort)
git commit --no-verify
# Note: CI may still block
```

---

### 5. "Orphaned worktrees"

**Symptoms:**
```bash
git worktree list
# Shows worktrees that shouldn't exist
```

**Diagnosis:**
```bash
bash .harness/scripts/cleanup-worktrees.sh
# Lists orphans
```

**Solutions:**
```bash
# Solution 1: Use cleanup script (interactive)
bash .harness/scripts/cleanup-worktrees.sh
# Answer 'y' to remove

# Solution 2: Manual removal
git worktree remove <path> --force

# Solution 3: Prune references
git worktree prune
```

---

### 6. "Pattern not matching as expected"

**Symptoms:**
- File matches pattern visually but not detected
- Or vice versa

**Diagnosis:**
```bash
# Test pattern manually
find . -name "*.tmp" ! -path "./.git/*"

# Check pattern file
cat .harness/cleanup_patterns.txt
```

**Solutions:**
```bash
# Solution 1: Fix pattern syntax
# Glob patterns: *.tmp, debug_*, test_*.py
# NOT regex: .*\.tmp won't work

# Solution 2: Test with find
find . -name "YOUR_PATTERN" ! -path "./.git/*"
```

---

### 7. "Git hooks disappeared after pull"

**Symptoms:**
- Hooks worked before
- After `git pull`, hooks don't run

**Cause:** Hooks are in `.git/` (not version controlled)

**Solutions:**
```bash
# Reinstall hooks after pull
bash .harness/install_hooks.sh

# Add to your pull routine
git pull && bash .harness/install_hooks.sh
```

---

### 8. "Workspace clean but validation fails"

**Symptoms:**
- No visible temp files
- Validation still reports violations

**Diagnosis:**
```bash
# Check hidden files
find . -name ".*tmp" ! -path "./.git/*"

# Check nested directories
bash .harness/scripts/validate-cleanup.sh
# Read output carefully
```

**Solutions:**
```bash
# Solution 1: Show hidden violations
bash .harness/scripts/validate-cleanup.sh | less

# Solution 2: Search specific pattern
find . -name "*.tmp" -o -name "debug_*"

# Solution 3: Nuclear option
bash .harness/scripts/auto-cleanup.sh
```

---

### 9. "ModuleNotFoundError: agent_harness"

**Symptoms:**
```
ModuleNotFoundError: No module named 'agent_harness'
```

**Solutions:**
```bash
# Solution 1: Install package
pip install -e .

# Solution 2: Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Solution 3: Use full path
python3 -c "import sys; sys.path.insert(0, 'src'); from agent_harness import SessionTracker"
```

---

### 10. "CI and local disagree"

**Symptoms:**
- Local validation passes
- CI validation fails

**Diagnosis:**
```bash
# Compare patterns
cat .harness/cleanup_patterns.txt

# Test same command as CI
git diff --name-only origin/main...HEAD | \
  grep -Ef .harness/cleanup_patterns.txt
```

**Solutions:**
```bash
# Solution 1: Update local
git pull origin main
bash .harness/install_hooks.sh

# Solution 2: Check CI logs
# Read GitHub Actions logs for exact command

# Solution 3: Sync patterns
git add .harness/cleanup_patterns.txt
git commit -m "chore: sync cleanup patterns"
```

---

## Emergency Procedures

### Complete Bypass (Break Glass)

**Only use for true emergencies (production down, critical hotfix)**
```bash
# 1. Bypass all validation
git commit --no-verify -m "EMERGENCY: description"
git push --no-verify

# 2. OR remove hooks temporarily
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled

# 3. Do your work
git commit -m "emergency fix"
git push

# 4. Restore hooks
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit

# 5. Clean up after emergency
bash .harness/scripts/auto-cleanup.sh
git commit -m "chore: cleanup after emergency"
git push

# 6. IMPORTANT: Document in post-incident review
```

### Reset Everything

**Nuclear option - start fresh**
```bash
# 1. Close any sessions
python check_protocol_compliance.py --close --skip-validation || true
rm -f .agent/sessions/session.lock

# 2. Clean workspace
bash .harness/scripts/auto-cleanup.sh

# 3. Clean worktrees
bash .harness/scripts/cleanup-worktrees.sh

# 4. Reinstall hooks
bash .harness/install_hooks.sh

# 5. Verify
bash .harness/scripts/status-dashboard.sh
```

---

## Getting Detailed Logs
```bash
# Session logs
cat .agent/sessions/sessions.jsonl | tail -10

# Override logs (audit trail)
cat .harness/cleanup_overrides.log 2>/dev/null || echo "No overrides logged"

# Git hook logs (if verbose enabled)
GIT_TRACE=1 git commit -m "test"
```

---

## Contact & Escalation

1. **Self-service:**
   - Read this guide
   - Check USER_GUIDE.md
   - Run diagnostics: `status-dashboard.sh`

2. **Team help:**
   - #agent-harness Slack channel
   - Tag @harness-maintainers

3. **Emergency:**
   - Use bypass procedures above
   - Document and review after
   - Create post-incident issue
