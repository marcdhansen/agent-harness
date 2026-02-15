# Beads GitHub Integration - Changelog

## Version 2.1 (2025-02-14)

### New: Safe Deployment Strategy

**Added comprehensive implementation order:**
- 6-step rollout process (including parallel run)
- Step 3.5: Parallel workflow validation strategy
- Comparison checklist for old vs new workflows
- Per-step testing instructions

**Why this matters:** Eliminates "big bang" deployment risk. Teams can validate the new workflow before deleting the old one.

### New: Python/pytest/ruff Support

**Added complete Python workflow examples:**
- PR CI workflow with pytest/ruff
- Post-merge CI workflow for Python
- Pre-commit configuration examples
- Language comparison table

**Python-specific features:**
- Direct tool invocation (vs npm scripts)
- Bandit for security scanning
- pytest with coverage reporting
- Ruff for both linting and formatting

### New: Workflow Behavior Documentation

**Added comprehensive behavior matrix:**
- Complete check matrix (pre-commit/PR/post-merge)
- Behavior definitions (blocks/warns/skips/creates issue)
- Philosophy explanations for each stage
- Language-specific notes

**Key clarification:** Tests block in PR CI (functional requirement), linting only warns (style requirement).

### Updated: FAQ Section

- Added Node.js vs Python guidance
- Added monorepo/mixed-language advice
- Clarified pre-commit framework choices

---

## Version 2.0 (2025-02-14)

### 1. ✅ Configurable Issue ID Regex Pattern

**Problem:** Hardcoded pattern `bd-[a-f0-9]{4,6}` only matched default beads format, breaking teams using custom formats like `agent-gbv.11`

**Solution:**
- All scripts now use configurable `BEADS_ISSUE_PATTERN` environment variable
- Defaults to standard beads pattern, but customizable via:
  - GitHub repository variables (recommended)
  - Environment variables in agent scripts
  - Hardcoded in workflows (not recommended)

**Configuration:**
```yaml
# In GitHub: Settings → Actions → Variables
BEADS_ISSUE_PATTERN = agent-\w+(?:\.\d+)?
```

**Example patterns:**
- Default beads: `bd-[a-f0-9]{4,6}(?:\.\d+)?`
- Custom agent: `agent-\w+(?:\.\d+)?`  
- Jira-style: `[A-Z]+-\d+`

### 2. ✅ Protected Branch Support

**Problem:** CI attempting to push directly to protected `main` branch causes workflow failures

**Solution:**
- Auto-detects protected branch push failures
- Automatically switches to metadata branch (`beads-metadata`)
- No manual intervention required
- Configurable via `BEADS_METADATA_BRANCH` variable

**How it works:**
```yaml
- name: Commit and push beads changes
  run: |
    # Try main branch
    if ! git push origin main 2>&1 | tee /tmp/push.log; then
      # Detect protection error
      if grep -q "protected branch" /tmp/push.log; then
        # Auto-switch to metadata branch
        git checkout -b beads-metadata
        git push origin beads-metadata
      fi
    fi
```

### 3. ✅ Pinned Beads Version

**Problem:** Using `main` branch for installation causes reproducibility issues and potential breaking changes

**Solution:**
- Beads version now explicitly pinned via `BEADS_VERSION` variable
- Default: `0.29.0`
- Includes version verification step
- Clear upgrade path via variable update

**Configuration:**
```yaml
# In GitHub workflow or variables
BEADS_VERSION: "0.29.0"
```

**Installation now:**
```yaml
- name: Install beads
  env:
    BEADS_VERSION: "0.29.0"
  run: |
    curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/v${BEADS_VERSION}/scripts/install.sh | bash
    bd --version  # Verify installation
```

## New Feature: Multi-Agent Orchestration

### Complete Implementation

**Why:** Research shows separate development and review agents catch more bugs and reduce confirmation bias.

**Components added:**

1. **Orchestrator Script** (`scripts/orchestrator.sh`)
   - Assigns work to developer agents
   - Creates review tasks for different reviewer agents
   - Enforces policy: reviewer ≠ developer
   - Monitors review approvals
   - Triggers CI/CD only after approval

2. **Developer Agent Workflow**
   - Accepts assigned work
   - Implements features
   - Marks as "completed" (NOT closed)
   - Orchestrator then creates review task

3. **Reviewer Agent Workflow**
   - Accepts review assignments
   - Reviews code from different agent
   - Approves or requests changes
   - Closes both review and original issue on approval

4. **CI/CD Review Enforcement**
   - Verifies review approval before running tests
   - Checks developer ≠ reviewer
   - Blocks builds without proper review
   - Full policy enforcement

### Configuration

```yaml
# .beads/config.yaml
orchestration:
  enabled: true
  agents:
    developers: [dev-agent-1, dev-agent-2, dev-agent-3]
    reviewers: [review-agent-1, review-agent-2]
  policies:
    require_different_reviewer: true
    min_reviewers: 1
```

### Workflow

```
Orchestrator → Assign to Dev Agent 1
              ↓
        Dev implements feature
              ↓
        Dev marks complete (not closed)
              ↓
Orchestrator → Create review task for Review Agent 2
              ↓
        Review Agent 2 reviews code
              ↓
        Approve → Close both issues → Trigger CI/CD
        Reject → Reassign to developer
```

## Documentation Improvements

### Added Sections

1. **Critical Setup Checklist** - Prominent warnings about required configuration
2. **Critical Configuration** - Detailed explanation of all three fixes
3. **Multi-Agent Orchestration** - Complete implementation guide
4. **Example Patterns** - Common regex patterns for different ID formats
5. **Protected Branch Details** - Step-by-step handling

### Updated Sections

- **Step 1 Workflow** - All critical fixes integrated
- **Agent Instructions** - Pattern configuration added
- **Troubleshooting** - New entries for pattern and branch issues
- **FAQ** - Questions about custom formats and orchestration

## Migration Guide

### For Existing Installations

**If using default beads IDs (`bd-xxxx`):**
- No changes required
- Optionally pin version for stability

**If using custom ID format:**
1. Identify your pattern (e.g., `agent-\w+(?:\.\d+)?`)
2. Add `BEADS_ISSUE_PATTERN` variable to GitHub repository
3. Update agent scripts to export pattern
4. Test pattern with one issue first

**If using protected branches:**
1. Add `BEADS_METADATA_BRANCH` variable
2. Run `bd init --branch beads-metadata`
3. Update workflow will auto-handle

**To add multi-agent orchestration:**
1. Create orchestrator, developer, and reviewer scripts
2. Configure `.beads/config.yaml`
3. Add review enforcement step to CI/CD workflow
4. Assign agent IDs and roles

## Testing Recommendations

### Before Production Deployment

1. **Test pattern matching:**
   ```bash
   echo "agent-gbv.11: test commit" | grep -oP "$BEADS_ISSUE_PATTERN"
   # Should output: agent-gbv.11
   ```

2. **Test protected branch handling:**
   ```bash
   # Enable branch protection temporarily
   # Run workflow
   # Verify metadata branch created
   # Verify no errors
   ```

3. **Test version pinning:**
   ```bash
   bd --version
   # Should match BEADS_VERSION
   ```

4. **Test orchestration:**
   ```bash
   # Create test issue
   # Run orchestrator
   # Verify developer assigned
   # Mark complete
   # Run orchestrator
   # Verify review created with different agent
   ```

## Breaking Changes

**None.** Version 2.0 is fully backward compatible:
- Defaults maintain v1.0 behavior
- New features are opt-in
- Custom patterns require explicit configuration

## Upgrade Checklist

- [ ] Review Critical Setup Checklist
- [ ] Configure BEADS_ISSUE_PATTERN (if needed)
- [ ] Set BEADS_VERSION to current stable
- [ ] Configure BEADS_METADATA_BRANCH (if protected)
- [ ] Test workflow on feature branch
- [ ] Deploy orchestration (optional)
- [ ] Update team documentation

## Support

Questions or issues? Check:
1. Critical Configuration section for detailed setup
2. Troubleshooting section for common problems
3. GitHub Actions logs for workflow issues
4. Beads repo: https://github.com/steveyegge/beads

---

**Version:** 2.0  
**Released:** 2025-02-14  
**Backward Compatible:** Yes  
**Migration Required:** Only if using custom ID formats or protected branches
