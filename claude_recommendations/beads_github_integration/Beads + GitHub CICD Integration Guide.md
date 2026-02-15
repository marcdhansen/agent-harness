# Beads + GitHub CI/CD Integration Guide

## Overview

This guide explains how to integrate [Beads](https://github.com/steveyegge/beads) (a git-based issue tracker) with GitHub Actions CI/CD pipelines to automatically manage issues based on build success/failure.

**The workflow:**
1. Developer/agent creates issues using `bd` CLI
2. Work is tracked in git via `.beads/` directory
3. PR references beads issue IDs (e.g., "Fixes bd-a1b2")
4. CI/CD runs on merge to main
5. **Success**: Auto-close referenced issues
6. **Failure**: Auto-create new issue with failure details
7. Changes sync back via git - all agents see updated state

**Key benefits:**
- ✅ No manual CI/CD babysitting
- ✅ Git-native (no external databases)
- ✅ Full audit trail in git history
- ✅ AI agent friendly (automatic sync)
- ✅ Works offline

## Prerequisites

- Beads installed locally: `curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash`
- Repository initialized: `bd init`
- GitHub Actions enabled in your repository

## ⚠️ Critical Setup Checklist

**Before implementing, configure these three critical settings:**

1. **✅ Set your issue ID pattern** (if not using default `bd-xxxx` format)
   - Go to repo Settings → Actions → Variables
   - Add `BEADS_ISSUE_PATTERN` with your regex (e.g., `agent-\w+(?:\.\d+)?`)

2. **✅ Pin beads version** for reproducibility
   - Add variable: `BEADS_VERSION = 0.29.0`
   - Or hardcode in workflow: `BEADS_VERSION: "0.29.0"`

3. **✅ Configure protected branch handling** (if main is protected)
   - Add variable: `BEADS_METADATA_BRANCH = beads-metadata`
   - Run: `bd init --branch beads-metadata`

See "Critical Configuration" section below for detailed instructions.

## Implementation Order (Safe Deployment)

**Follow this sequence for zero-risk deployment:**

### The 6-Step Rollout

```
1. CI skip headers        → No-op (safe, defense in depth)
2. Pre-commit stages      → Config change (local enforcement only)
3. New PR CI workflow     → Test in feature branch
3.5 Parallel run          → Both workflows side-by-side (1-2 days)
4. Delete old workflow    → After comparison proves equivalence
5. Post-merge CI          → After PR CI validated
6. Full PR test           → End-to-end validation
```

### Why This Order?

- ✅ **Incremental** - Each step independently testable
- ✅ **Safe** - Easy rollback at any point
- ✅ **Validated** - Parallel run catches edge cases
- ✅ **No big bang** - Gradual transition with monitoring

### Step 3.5: Parallel Run Strategy (Critical!)

**Before deleting your old workflow, run both in parallel:**

**Duration:** 1-2 days (5-10 PRs minimum)

**Comparison checklist:**

```bash
# scripts/compare-workflows.sh
#!/bin/bash

echo "Comparing old vs new workflow results..."

# Get last 10 runs of each workflow
echo "Old workflow (linting.yaml or similar):"
gh run list --workflow=linting.yaml --limit=10 --json conclusion,name,createdAt

echo ""
echo "New workflow (pr-ci.yml):"
gh run list --workflow=pr-ci.yml --limit=10 --json conclusion,name,createdAt

echo ""
echo "Manual checks:"
echo "✓ Same pass/fail outcomes?"
echo "✓ Similar runtime (±20%)?"
echo "✓ New warnings caught anything old missed?"
echo "✓ Any false positives in new workflow?"
echo "✓ All blocking checks still blocking?"
```

**What to look for:**

| Scenario | Action |
|----------|--------|
| ✅ Both pass | Good - workflows equivalent |
| ✅ Both fail | Good - workflows equivalent |
| ⚠️ Old passes, new fails | Investigate - new workflow may be stricter (good) |
| 🚨 Old fails, new passes | **CRITICAL** - New workflow missing checks! |

**Only proceed to step 4 when confident both workflows are equivalent.**

### Step-by-Step Details

#### Step 1: Add CI Skip Headers

Add to all pre-commit hook scripts:

```bash
#!/bin/bash
# .git/hooks/pre-commit or in hook script

# CI SKIP HEADER - defense in depth
if [[ "$GITHUB_ACTIONS" == "true" ]] || [[ "$CI" == "true" ]]; then
    echo "ℹ️ Skipping in CI (pre-commit hooks are local development tools)"
    exit 0
fi

# Rest of hook logic...
```

**Test:** Hooks should work locally, skip in CI

#### Step 2: Configure Pre-Commit Stages

Update `.pre-commit-config.yaml`:

```yaml
# Only run hooks on local commits, not in CI
default_stages: [commit]

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        stages: [commit]  # Local only
      - id: ruff-format
        stages: [commit]  # Local only
```

**Test:** `pre-commit run --all-files` should run locally, skip when `CI=true`

#### Step 3: Create New PR CI Workflow

See "Setup" section below for full workflow examples.

**Test:** Create feature branch, open PR, verify new workflow runs

#### Step 3.5: Run Both Workflows in Parallel

Keep old workflow enabled alongside new workflow.

**Monitor for 1-2 days:**
- Compare outcomes
- Check for discrepancies
- Validate new workflow catches everything

#### Step 4: Delete Old Workflow

Only after parallel run proves equivalence:

```bash
git rm .github/workflows/linting.yaml
git commit -m "ci: remove old linting workflow (replaced by pr-ci.yml)"
```

#### Step 5: Create Post-Merge CI

See "Post-Merge CI" section below.

**Test:** Merge a PR, verify post-merge workflow runs

#### Step 6: Full PR Test

Create test PR that:
- Passes all checks
- Triggers issue close on merge
- Validates end-to-end flow

## Setup

### Language-Specific Examples

This guide provides examples for both **Node.js/npm** and **Python/pytest/ruff** projects. Choose the appropriate section for your stack.

### Quick Comparison

| Aspect | Node.js/npm | Python/pytest/ruff |
|--------|-------------|-------------------|
| **Linter** | ESLint (`npm run lint`) | Ruff (`ruff check .`) |
| **Formatter** | Prettier (`npm run format`) | Ruff Format (`ruff format .`) |
| **Unit Tests** | Jest/Vitest (`npm test`) | pytest (`pytest tests/unit`) |
| **Security** | npm audit | Bandit (`bandit -r src/`) |
| **Type Checking** | TypeScript (`tsc`) | mypy (`mypy src/`) (optional) |
| **Pre-commit** | Husky + lint-staged | pre-commit framework |

### Key Differences

**Node.js:**
- Uses `package.json` scripts (e.g., `npm run lint`)
- Pre-commit typically via Husky
- `npm audit` for security

**Python:**
- Direct tool invocation (e.g., `ruff check .`)
- Pre-commit via `.pre-commit-config.yaml`
- Bandit for security scanning
- pytest with coverage via `--cov` flag

---

## Node.js/TypeScript Projects

### Step 1: Create GitHub Actions Workflow (Node)

Create `.github/workflows/pr-ci.yml`:

```yaml
name: PR Validation (Node)

on:
  pull_request:
    branches: [main, dev]

permissions:
  contents: read
  pull-requests: write

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install beads
        env:
          BEADS_VERSION: "0.29.0"
        run: |
          curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/v${BEADS_VERSION}/scripts/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      # ============================================
      # QUALITY VERIFICATION (Non-Blocking)
      # ============================================
      - name: Verify linting
        run: |
          if npm run lint; then
            echo "✅ Linting passed"
          else
            echo "::warning::Linting failed - pre-commit hook may not have run"
          fi
        continue-on-error: true
      
      - name: Verify formatting
        run: |
          if npm run format:check; then
            echo "✅ Formatting passed"
          else
            echo "::warning::Formatting failed - run: npm run format"
          fi
        continue-on-error: true
      
      # ============================================
      # FUNCTIONAL GATES (Blocking)
      # ============================================
      - name: Run unit tests
        run: npm run test:unit
      
      - name: Run integration tests
        run: npm run test:integration
      
      - name: Build
        run: npm run build
      
      - name: Security scan
        run: npm audit --audit-level=moderate
```

---

## Python Projects

### Step 1: Create GitHub Actions Workflow (Python)

Create `.github/workflows/pr-ci.yml`:

```yaml
name: PR Validation (Python)

on:
  pull_request:
    branches: [main, dev]

permissions:
  contents: read
  pull-requests: write

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install beads
        env:
          BEADS_VERSION: "0.29.0"
        run: |
          curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/v${BEADS_VERSION}/scripts/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff bandit
      
      # ============================================
      # QUALITY VERIFICATION (Non-Blocking)
      # ============================================
      - name: Verify linting
        run: |
          echo "::group::Linting Verification"
          if ruff check .; then
            echo "✅ Linting passed"
          else
            echo "::warning::Linting failed - pre-commit hook may not have run"
            echo "Fix with: ruff check --fix . && git commit --amend"
          fi
          echo "::endgroup::"
        continue-on-error: true
      
      - name: Verify formatting
        run: |
          echo "::group::Formatting Verification"
          if ruff format --check .; then
            echo "✅ Formatting passed"
          else
            echo "::warning::Formatting issues detected"
            echo "Fix with: ruff format . && git commit --amend"
          fi
          echo "::endgroup::"
        continue-on-error: true
      
      # ============================================
      # FUNCTIONAL GATES (Blocking)
      # ============================================
      - name: Run unit tests
        run: pytest tests/unit -v --cov=src --cov-report=term
      
      - name: Run integration tests
        run: pytest tests/integration -v
      
      - name: Security scan
        run: bandit -r src/ -ll
      
      - name: Type checking (if using mypy)
        run: mypy src/
        continue-on-error: true  # Optional: make this blocking if desired
```

### Pre-Commit Configuration (Python)

`.pre-commit-config.yaml`:

```yaml
default_stages: [commit]  # Only run on local commits

repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
        stages: [commit]
      
      - id: ruff-format
        stages: [commit]
  
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest (unit tests only)
        entry: pytest tests/unit -v
        language: system
        pass_filenames: false
        stages: [commit]
```

---

## Post-Merge CI (Both Stacks)

### Node.js Post-Merge CI

Create `.github/workflows/beads-integration.yml`:

```yaml
name: Beads Issue Automation

on:
  push:
    branches: [main]

# CRITICAL: Grant write permissions for pushing beads updates
permissions:
  contents: write

jobs:
  ci-with-beads:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Need full history for beads
      
      # FIXED: Pin beads version for reproducibility
      - name: Install beads
        env:
          BEADS_VERSION: "0.29.0"  # UPDATE THIS when upgrading beads
        run: |
          curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/v${BEADS_VERSION}/scripts/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH
          bd --version  # Verify installation
      
      - name: Initialize beads
        run: |
          if [ ! -d ".beads" ]; then
            bd init --quiet
          fi
          bd sync  # Ensure we have latest issues
      
      # ============================================
      # YOUR CI/CD STEPS HERE
      # ============================================
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        id: tests
        run: npm test
        continue-on-error: true
      
      - name: Run build
        id: build
        if: steps.tests.outcome == 'success'
        run: npm run build
        continue-on-error: true
      
      - name: Run linter
        id: lint
        if: steps.tests.outcome == 'success' && steps.build.outcome == 'success'
        run: npm run lint
        continue-on-error: true
      
      # FIXED: Configurable issue ID regex pattern
      # Default: bd-[a-f0-9]{4,6}(?:\.\d+)?
      # Custom: agent-\w+(?:\.\d+)? (for agent-gbv.11 format)
      # Set via repository variable: BEADS_ISSUE_PATTERN
      - name: Extract linked issues from commits
        id: extract_issues
        env:
          # CONFIGURE THIS: Set in GitHub repo settings > Secrets and variables > Actions > Variables
          # Or hardcode your pattern here
          ISSUE_PATTERN: ${{ vars.BEADS_ISSUE_PATTERN || 'bd-[a-f0-9]{4,6}(?:\.\d+)?' }}
        uses: actions/github-script@v7
        with:
          script: |
            const commits = context.payload.commits || [];
            const pattern = process.env.ISSUE_PATTERN;
            
            console.log(`Using issue ID pattern: ${pattern}`);
            const issueRegex = new RegExp(pattern, 'gi');
            const issues = new Set();
            
            for (const commit of commits) {
              const matches = commit.message.match(issueRegex);
              if (matches) {
                matches.forEach(id => issues.add(id));
                console.log(`Found in commit "${commit.message}": ${matches.join(', ')}`);
              }
            }
            
            console.log(`Total unique issues found: ${Array.from(issues).join(', ')}`);
            return Array.from(issues);
      
      - name: Close issues on success
        if: |
          steps.tests.outcome == 'success' && 
          steps.build.outcome == 'success' && 
          steps.lint.outcome == 'success'
        run: |
          ISSUES='${{ steps.extract_issues.outputs.result }}'
          echo "Issues found: $ISSUES"
          
          if [ "$ISSUES" != "[]" ]; then
            echo "$ISSUES" | jq -r '.[]' | while read -r issue_id; do
              echo "Closing $issue_id"
              bd close "$issue_id" --reason "✅ CI/CD passed successfully" --json || true
            done
            
      # FIXED: Handle protected branches
      - name: Commit and push beads changes
        if: success() || failure()  # Always try to commit beads updates
        env:
          BEADS_BRANCH: ${{ vars.BEADS_METADATA_BRANCH || 'beads-metadata' }}
        run: |
          if [ -z "$(git status --porcelain .beads/)" ]; then
            echo "No beads changes to commit"
            exit 0
          fi
          
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .beads/
          
          # Detect if current branch is protected
          CURRENT_BRANCH="${{ github.ref_name }}"
          
          # Try to push to current branch first
          if git commit -m "beads: auto-update issues from CI/CD [skip ci]" && \
             git push origin "$CURRENT_BRANCH" 2>&1 | tee /tmp/push.log; then
            echo "✓ Pushed beads updates to $CURRENT_BRANCH"
          else
            # If push failed, assume protected branch - use metadata branch
            if grep -q "protected branch" /tmp/push.log || grep -q "permission" /tmp/push.log; then
              echo "⚠ Branch $CURRENT_BRANCH is protected, using $BEADS_BRANCH instead"
              
              # Reset the commit since it failed
              git reset HEAD~1
              
              # Fetch and checkout metadata branch
              git fetch origin "$BEADS_BRANCH" || git checkout -b "$BEADS_BRANCH"
              git checkout "$BEADS_BRANCH" || git checkout -b "$BEADS_BRANCH"
              
              # Cherry-pick beads changes only
              git add .beads/
              git commit -m "beads: auto-update issues from CI/CD [skip ci]"
              git push origin "$BEADS_BRANCH"
              
              echo "✓ Pushed beads updates to $BEADS_BRANCH (protected branch workflow)"
            else
              echo "❌ Push failed for unknown reason:"
              cat /tmp/push.log
              exit 1
            fi
          fi
          fi
      
      - name: Create issue on failure
        if: |
          steps.tests.outcome == 'failure' || 
          steps.build.outcome == 'failure' || 
          steps.lint.outcome == 'failure'
        run: |
          # Determine which step failed
          FAILED_STEP="unknown"
          if [ "${{ steps.tests.outcome }}" = "failure" ]; then
            FAILED_STEP="tests"
          elif [ "${{ steps.build.outcome }}" = "failure" ]; then
            FAILED_STEP="build"
          elif [ "${{ steps.lint.outcome }}" = "failure" ]; then
            FAILED_STEP="lint"
          fi
          
          # Create beads issue
          ISSUE_OUTPUT=$(bd create "CI/CD Failure: $FAILED_STEP failed on main" \
            -t bug \
            -p 0 \
            -l "ci-failure,automated" \
            -d "CI/CD pipeline failed during $FAILED_STEP step.

**Workflow:** ${{ github.workflow }}
**Run:** ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
**Commit:** ${{ github.sha }}
**Branch:** ${{ github.ref_name }}
**Triggered by:** @${{ github.actor }}

## Next Steps
1. Review the workflow logs at the URL above
2. Determine if this is a code issue or infrastructure issue
3. Fix and re-run or create follow-up issues

cc: @${{ github.actor }}" \
            --json)
          
          ISSUE_ID=$(echo "$ISSUE_OUTPUT" | jq -r '.id')
          echo "Created issue: $ISSUE_ID"
          echo "issue_created=true" >> $GITHUB_OUTPUT
```

### Python Post-Merge CI

Create `.github/workflows/post-merge-ci.yml`:

```yaml
name: Post-Merge Safety Net (Python)

on:
  push:
    branches: [main, dev]

permissions:
  contents: write

jobs:
  safety-net:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 10  # For potential auto-revert
      
      - name: Install beads
        env:
          BEADS_VERSION: "0.29.0"
        run: |
          curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/v${BEADS_VERSION}/scripts/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Initialize beads
        run: |
          bd init --quiet
          bd sync
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov bandit
      
      # ============================================
      # SAFETY NET CHECKS (Non-Blocking)
      # ============================================
      - name: Run unit tests
        id: pytest_unit
        run: pytest tests/unit -v --cov=src
        continue-on-error: true
      
      - name: Run integration tests
        id: pytest_integration
        run: pytest tests/integration -v
        continue-on-error: true
      
      - name: Security scan
        id: security
        run: bandit -r src/ -ll
        continue-on-error: true
      
      # Extract referenced issues
      - name: Extract issues
        id: extract_issues
        env:
          ISSUE_PATTERN: ${{ vars.BEADS_ISSUE_PATTERN || 'bd-[a-f0-9]{4,6}(?:\.\d+)?' }}
        uses: actions/github-script@v7
        with:
          script: |
            const commits = context.payload.commits || [];
            const pattern = process.env.ISSUE_PATTERN;
            const issueRegex = new RegExp(pattern, 'gi');
            const issues = new Set();
            
            for (const commit of commits) {
              const matches = commit.message.match(issueRegex);
              if (matches) {
                matches.forEach(id => issues.add(id));
              }
            }
            
            return Array.from(issues);
      
      # Close issues if all checks passed
      - name: Close issues on success
        if: |
          steps.pytest_unit.outcome == 'success' &&
          steps.pytest_integration.outcome == 'success' &&
          steps.security.outcome == 'success'
        run: |
          ISSUES='${{ steps.extract_issues.outputs.result }}'
          
          if [ "$ISSUES" != "[]" ]; then
            echo "$ISSUES" | jq -r '.[]' | while read -r issue_id; do
              bd close "$issue_id" --reason "✅ All post-merge checks passed"
            done
          fi
      
      # Create P0 issue if critical checks fail
      - name: Create critical issue on failure
        if: |
          steps.pytest_unit.outcome == 'failure' ||
          steps.pytest_integration.outcome == 'failure' ||
          steps.security.outcome == 'failure'
        run: |
          FAILED=""
          [ "${{ steps.pytest_unit.outcome }}" = "failure" ] && FAILED="$FAILED\n- Unit tests"
          [ "${{ steps.pytest_integration.outcome }}" = "failure" ] && FAILED="$FAILED\n- Integration tests"
          [ "${{ steps.security.outcome }}" = "failure" ] && FAILED="$FAILED\n- Security scan"
          
          bd create "🚨 CRITICAL: Post-merge CI failure on ${{ github.ref_name }}" \
            -t bug \
            -p 0 \
            -l "ci-failure,critical,${{ github.ref_name }}-broken" \
            -d "Tests that passed in PR CI are now failing on ${{ github.ref_name }}.

**Failed checks:**$FAILED

**Possible causes:**
- Merge conflict resolution issue
- Environment differences between PR CI and post-merge
- Race condition in tests
- Infrastructure problem

**Action required:** Investigate immediately and either fix forward or revert.

**Commit:** ${{ github.sha }}
**Author:** @${{ github.actor }}
**Run:** ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      
      # Commit beads changes
      - name: Commit beads changes
        if: always()
        env:
          BEADS_BRANCH: ${{ vars.BEADS_METADATA_BRANCH || 'beads-metadata' }}
        run: |
          if [ -z "$(git status --porcelain .beads/)" ]; then
            exit 0
          fi
          
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add .beads/
          
          CURRENT_BRANCH="${{ github.ref_name }}"
          
          if git commit -m "beads: auto-update from post-merge CI [skip ci]" && \
             git push origin "$CURRENT_BRANCH" 2>&1 | tee /tmp/push.log; then
            echo "✓ Pushed to $CURRENT_BRANCH"
          else
            if grep -q "protected branch" /tmp/push.log; then
              git reset HEAD~1
              git fetch origin "$BEADS_BRANCH" || git checkout -b "$BEADS_BRANCH"
              git checkout "$BEADS_BRANCH"
              git add .beads/
              git commit -m "beads: auto-update from post-merge CI [skip ci]"
              git push origin "$BEADS_BRANCH"
              echo "✓ Pushed to $BEADS_BRANCH"
            fi
          fi
```

---

## Workflow Behavior Summary

### Complete Check Matrix

This table shows how each check behaves across all three CI stages:

| Check Type | Pre-Commit (Local) | PR CI | Post-Merge CI |
|------------|-------------------|-------|---------------|
| **Linting** (ruff/eslint) | ✅ **Blocks commit** | ⚠️ **Warns** (non-blocking) | ❌ **Skip** (not needed) |
| **Formatting** (ruff format/prettier) | ✅ **Blocks commit** | ❌ **Skip** (auto-fixable) | ❌ **Skip** |
| **Unit Tests** (pytest/jest) | ✅ **Blocks commit** | ✅ **Blocks merge** | 📋 **Create P0 issue** (if fails) |
| **Integration Tests** | ❌ Skip (can't run locally) | ✅ **Blocks merge** | 📋 **Create P0 issue** (if fails) |
| **E2E Tests** | ❌ Skip (can't run locally) | ✅ **Blocks merge** | 📋 **Create P0 issue** (if fails) |
| **Security Scan** | ❌ Skip (requires tools) | ✅ **Blocks merge** | 📋 **Create P0 issue** (if fails) |
| **Type Checking** (mypy/tsc) | ✅ **Blocks commit** | ✅ **Blocks merge** | 📋 **Create P0 issue** (if fails) |

### Behavior Definitions

- ✅ **Blocks** - Failure prevents the action (commit/merge/etc.)
- ⚠️ **Warns** - Failure logs warning but continues
- 📋 **Create Issue** - Failure creates beads issue but doesn't block
- ❌ **Skip** - Check doesn't run at this stage

### Why This Architecture?

**Pre-Commit (Local):**
- **Philosophy:** Catch everything early, fail fast
- **Goal:** Prevent broken code from entering git
- **Trade-off:** Slightly slower commits, but cleaner history

**PR CI:**
- **Philosophy:** Gate on functionality, warn on style
- **Goal:** Prevent broken code from reaching main
- **Trade-off:** Longer PR cycle, but protected main branch

**Post-Merge CI:**
- **Philosophy:** Safety net, never block
- **Goal:** Detect unexpected issues, track for fixes
- **Trade-off:** Issues need manual resolution, but no blocking

### Python-Specific Notes

**Ruff combines linting + formatting:**
```bash
# Pre-commit runs both
ruff check --fix .    # Lint with auto-fix
ruff format .         # Format

# PR CI only verifies linting (formatting is trivial)
ruff check .          # Verify (warns if fails)

# Post-merge CI skips both (already verified)
```

**Pytest structure matters:**
```bash
# Pre-commit: Only fast unit tests
pytest tests/unit -v

# PR CI: Unit + integration
pytest tests/unit -v
pytest tests/integration -v

# Post-merge: Re-run critical checks
pytest tests/unit -v --cov=src
pytest tests/integration -v
```

### Node-Specific Notes

**ESLint + Prettier separation:**
```bash
# Pre-commit runs both
npm run lint:fix      # ESLint with auto-fix
npm run format        # Prettier

# PR CI only verifies linting
npm run lint          # Verify (warns if fails)

# Post-merge CI skips both
```

**Test structure:**
```bash
# Pre-commit: Fast unit tests only
npm run test:unit

# PR CI: All tests
npm run test:unit
npm run test:integration
npm run test:e2e

# Post-merge: Re-run critical
npm run test:unit
npm run test:integration
```

---

### Step 2: Update Agent Instructions

Add this section to your `AGENTS.md` or equivalent:

```markdown
## Issue Tracking with Beads + CI/CD

### For AI Agents

**Before starting work:**
```bash
bd sync                    # Sync with git
bd ready --json            # Find ready work
bd show bd-a1b2 --json     # Review issue details
```

**During work:**
```bash
# Reference issue in commits
git commit -m "bd-a1b2: implement authentication"

# Create new issues for discovered work
bd create "Fix validation bug" -t bug -p 1 -l backend
bd dep add bd-f14c bd-a1b2 --type discovered-from

# Update status
bd update bd-a1b2 --status in_progress
```

**After completing work:**
```bash
# Close the issue
bd close bd-a1b2 --reason "Implemented and tested"

# Sync changes
bd sync
git add .beads/
git commit -m "beads: close bd-a1b2"
git push
```

**Important:** CI/CD will automatically:
- Close issues when builds succeed (if referenced in commits)
- Create issues when builds fail
- Sync everything back via git

### Commit Message Convention

Reference beads issues in commit messages using the issue ID:

```
bd-a1b2: add user authentication
bd-f14c: fix validation edge case
bd-3e7a: refactor database queries
```

The CI/CD pipeline will automatically close these issues on successful merge.

### PR Description Convention

For clearer tracking, also reference issues in PR descriptions:

```markdown
## Changes
- Implemented user authentication
- Added password hashing
- Created login endpoint

Fixes bd-a1b2
Addresses bd-f14c
```
```

## Usage Examples

### Example 1: Feature Development

```bash
# Agent finds ready work
$ bd ready --json | jq '.[0]'
{
  "id": "bd-a1b2",
  "title": "Implement user authentication",
  "priority": 1,
  "status": "open"
}

# Agent starts work
$ bd update bd-a1b2 --status in_progress
$ git commit -m "bd-a1b2: add login endpoint"
$ git commit -m "bd-a1b2: implement password hashing"

# Agent completes work
$ bd close bd-a1b2 --reason "Completed and tested"
$ git push

# CI/CD runs successfully
# Issue bd-a1b2 stays closed (already handled by agent)
```

### Example 2: CI/CD Failure Handling

```bash
# Agent pushes code
$ git push origin feature-branch

# PR merged to main
# CI/CD fails during tests

# CI/CD automatically creates issue:
# bd-f14c: "CI/CD Failure: tests failed on main"

# Agent pulls latest
$ git pull
$ bd sync

# Agent sees new issue
$ bd ready --json
[
  {
    "id": "bd-f14c",
    "title": "CI/CD Failure: tests failed on main",
    "priority": 0,
    "labels": ["ci-failure", "automated"]
  }
]

# Agent investigates and fixes
$ bd update bd-f14c --status in_progress
$ git commit -m "bd-f14c: fix broken test"
$ bd close bd-f14c --reason "Fixed failing test"
$ git push

# CI/CD succeeds, issue stays closed
```

### Example 3: Multiple Issues in One PR

```bash
# Agent works on related issues
$ bd update bd-a1b2 --status in_progress
$ bd update bd-f14c --status in_progress

# Reference both in commits
$ git commit -m "bd-a1b2: implement auth"
$ git commit -m "bd-f14c: add validation"

# Close both
$ bd close bd-a1b2 bd-f14c --reason "Completed"
$ git push

# CI/CD succeeds - both issues remain closed
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Developer/Agent Workflow                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Find work:     bd ready --json                         │
│  2. Start work:    bd update bd-a1b2 --status in_progress  │
│  3. Make commits:  git commit -m "bd-a1b2: implement auth" │
│  4. Close issue:   bd close bd-a1b2                        │
│  5. Push:          git push                                │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ CI/CD Pipeline (GitHub Actions)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Install beads                                          │
│  2. Sync beads database                                    │
│  3. Run tests, build, lint                                 │
│  4. Extract issue IDs from commits                         │
│                                                             │
│     ┌─────────────┐                                        │
│     │   Success?  │                                        │
│     └──────┬──────┘                                        │
│            │                                               │
│     ┌──────┴──────┐                                        │
│     ▼             ▼                                        │
│   YES            NO                                        │
│     │             │                                        │
│     │             ├─ Create issue: "CI/CD Failure"        │
│     │             ├─ Priority 0, label: ci-failure        │
│     │             └─ Commit & push                        │
│     │                                                      │
│     ├─ Close referenced issues                            │
│     └─ Commit & push                                       │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent Pulls Updates                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  git pull → bd sync → bd ready                             │
│                                                             │
│  Sees updated issue states automatically                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Multi-Agent Orchestration

### Enforcing Separate Development and Review Agents

**Best practice:** Different agents should handle development vs. code review to ensure fresh perspective and catch more issues.

**Orchestrator responsibilities:**
1. Assign work to developer agents
2. Create review tasks for different reviewer agents
3. Enforce policy: reviewer ≠ developer
4. Coordinate handoffs via beads status and dependencies
5. Trigger CI/CD only after review approval

### Orchestrator Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ Orchestrator Agent                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Find ready work: bd ready --json                       │
│  2. Assign to developer agent: bd update bd-a1b2           │
│     --assignee dev-agent-1 --status in_progress            │
│  3. Monitor completion (developer closes issue)            │
│  4. Create review task: bd create "Review bd-a1b2"         │
│     --assignee review-agent-1                              │
│     (dep: bd dep add bd-f14c bd-a1b2 --type blocks)        │
│  5. Monitor review completion                              │
│  6. If approved: merge PR → CI/CD runs                     │
│  7. If rejected: reassign to developer or new dev agent    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Developer    │  │ Reviewer     │  │ CI/CD        │
│ Agent 1      │  │ Agent 1      │  │ Pipeline     │
│              │  │              │  │              │
│ Work on      │  │ Review       │  │ Auto-close   │
│ bd-a1b2      │  │ bd-f14c      │  │ or create    │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Implementation Pattern

#### 1. Agent Naming Convention

Use consistent agent identifiers:
```bash
# Developer agents
export AGENT_ID="dev-agent-1"
export AGENT_ROLE="developer"

# Reviewer agents  
export AGENT_ID="review-agent-1"
export AGENT_ROLE="reviewer"

# Orchestrator
export AGENT_ID="orchestrator"
export AGENT_ROLE="orchestrator"
```

#### 2. Orchestrator Script

Create `scripts/orchestrator.sh`:

```bash
#!/bin/bash
set -e

# Orchestrator configuration
ORCHESTRATOR_ID="orchestrator"
DEVELOPER_AGENTS=("dev-agent-1" "dev-agent-2" "dev-agent-3")
REVIEWER_AGENTS=("review-agent-1" "review-agent-2")

# Function: Assign work to developer
assign_development_work() {
    local issue_id=$1
    local dev_agent=$2
    
    echo "Assigning $issue_id to developer $dev_agent"
    
    bd update "$issue_id" \
        --assignee "$dev_agent" \
        --status in_progress \
        --json
    
    # Add note about assignment
    bd update "$issue_id" \
        --notes "Assigned to $dev_agent by $ORCHESTRATOR_ID at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

# Function: Create review task for different agent
create_review_task() {
    local dev_issue_id=$1
    local dev_agent=$2
    local review_agent=$3
    
    # Policy enforcement: reviewer must be different from developer
    if [ "$dev_agent" = "$review_agent" ]; then
        echo "ERROR: Reviewer cannot be the same as developer"
        return 1
    fi
    
    echo "Creating review task for $dev_issue_id (dev: $dev_agent, reviewer: $review_agent)"
    
    # Get original issue details
    local issue_info=$(bd show "$dev_issue_id" --json)
    local issue_title=$(echo "$issue_info" | jq -r '.title')
    
    # Create review issue
    local review_issue=$(bd create "Review: $issue_title" \
        -t task \
        -p 1 \
        -l "review,code-review" \
        --assignee "$review_agent" \
        -d "Code review for $dev_issue_id

**Developer:** $dev_agent
**Original Issue:** $dev_issue_id

## Review Checklist
- [ ] Code quality and style
- [ ] Test coverage
- [ ] Security considerations  
- [ ] Performance implications
- [ ] Documentation updates

## Instructions
1. Review the PR/branch associated with $dev_issue_id
2. If approved: close this issue with --reason 'Approved'
3. If changes needed: update $dev_issue_id with notes and reassign" \
        --json)
    
    local review_issue_id=$(echo "$review_issue" | jq -r '.id')
    
    # Create blocking dependency: review must happen before original issue is truly "done"
    bd dep add "$review_issue_id" "$dev_issue_id" --type blocks
    
    echo "Created review issue: $review_issue_id"
    echo "$review_issue_id"
}

# Function: Select next available agent from pool
select_agent() {
    local agent_pool=("$@")
    local agent_count=${#agent_pool[@]}
    
    # Round-robin or random selection
    local index=$((RANDOM % agent_count))
    echo "${agent_pool[$index]}"
}

# Function: Get developer who worked on issue
get_issue_developer() {
    local issue_id=$1
    bd show "$issue_id" --json | jq -r '.assignee // empty'
}

# Function: Check if issue needs review
needs_review() {
    local issue_id=$1
    
    # Check if issue is closed and has no open review task
    local status=$(bd show "$issue_id" --json | jq -r '.status')
    if [ "$status" != "closed" ]; then
        return 1
    fi
    
    # Check for existing review issues
    local review_count=$(bd list --title-contains "Review: " --status open --json | \
        jq "[.[] | select(.description | contains(\"$issue_id\"))] | length")
    
    if [ "$review_count" -gt 0 ]; then
        return 1  # Review already exists
    fi
    
    return 0  # Needs review
}

# Main orchestration loop
orchestrate() {
    echo "Starting orchestration cycle..."
    
    # 1. Find work that needs assignment
    local ready_work=$(bd ready --json | jq -r '.[] | select(.assignee == null) | .id')
    
    for issue_id in $ready_work; do
        local dev_agent=$(select_agent "${DEVELOPER_AGENTS[@]}")
        assign_development_work "$issue_id" "$dev_agent"
    done
    
    # 2. Find completed work that needs review
    local completed_work=$(bd list --status closed --json | \
        jq -r '.[] | select(.labels | contains(["review"]) | not) | .id')
    
    for issue_id in $completed_work; do
        if needs_review "$issue_id"; then
            local dev_agent=$(get_issue_developer "$issue_id")
            
            # Select reviewer different from developer
            local review_agent=""
            for agent in "${REVIEWER_AGENTS[@]}"; do
                if [ "$agent" != "$dev_agent" ]; then
                    review_agent=$agent
                    break
                fi
            done
            
            if [ -n "$review_agent" ]; then
                create_review_task "$issue_id" "$dev_agent" "$review_agent"
            else
                echo "WARNING: No available reviewer different from $dev_agent"
            fi
        fi
    done
    
    # 3. Check review approvals and trigger merges
    local approved_reviews=$(bd list --status closed --label review --json | \
        jq -r '.[] | select(.close_reason | contains("Approved")) | .id')
    
    for review_id in $approved_reviews; do
        # Extract original issue ID from review description
        # Use configurable pattern from config or default
        local issue_pattern="${BEADS_ISSUE_PATTERN:-bd-[a-f0-9]{4,6}(?:\\.\\d+)?}"
        local original_issue=$(bd show "$review_id" --json | \
            jq -r ".description | match(\"\\\\b($issue_pattern)\\\\b\") | .string")
        
        echo "Review $review_id approved. Original issue: $original_issue"
        echo "Ready to merge and trigger CI/CD"
        
        # Signal to merge (this would trigger your git workflow)
        # Could push to a merge-queue branch, update PR labels, etc.
    done
    
    echo "Orchestration cycle complete"
}

# Run orchestration
orchestrate
```

#### 3. Developer Agent Workflow

Developer agents should follow this pattern:

```bash
#!/bin/bash
# Developer agent script

AGENT_ID=${AGENT_ID:-"dev-agent-1"}

# 1. Check for assigned work
my_work=$(bd list --assignee "$AGENT_ID" --status in_progress --json)

if [ "$(echo "$my_work" | jq 'length')" -eq 0 ]; then
    echo "No work assigned to $AGENT_ID"
    exit 0
fi

issue_id=$(echo "$my_work" | jq -r '.[0].id')
echo "Working on $issue_id"

# 2. Do the work
# ... implement feature, write code, run tests ...

# 3. Commit with issue reference
git add .
git commit -m "$issue_id: implement feature"

# 4. Mark as complete (NOT closed - review hasn't happened yet)
bd update "$issue_id" --status completed --json
bd update "$issue_id" --notes "Development complete. Ready for review."

# 5. DO NOT close the issue - orchestrator will create review task
echo "Development complete. Waiting for orchestrator to assign reviewer."
```

#### 4. Reviewer Agent Workflow

Reviewer agents should follow this pattern:

```bash
#!/bin/bash
# Reviewer agent script

AGENT_ID=${AGENT_ID:-"review-agent-1"}

# 1. Check for assigned reviews
my_reviews=$(bd list --assignee "$AGENT_ID" --status open --label review --json)

if [ "$(echo "$my_reviews" | jq 'length')" -eq 0 ]; then
    echo "No reviews assigned to $AGENT_ID"
    exit 0
fi

review_id=$(echo "$my_reviews" | jq -r '.[0].id')
echo "Reviewing $review_id"

# 2. Get original issue for context
# Use configurable pattern
issue_pattern="${BEADS_ISSUE_PATTERN:-bd-[a-f0-9]{4,6}(?:\\.\\d+)?}"
original_issue=$(bd show "$review_id" --json | \
    jq -r ".description | match(\"\\\\b($issue_pattern)\\\\b\") | .string")

echo "Original issue: $original_issue"

# 3. Perform code review
# ... check code quality, tests, security, etc ...

# 4. Decision: Approve or Request Changes
review_decision="approved"  # or "changes_requested"

if [ "$review_decision" = "approved" ]; then
    # Close review issue
    bd close "$review_id" --reason "Approved - code meets quality standards"
    
    # Close original development issue
    bd close "$original_issue" --reason "Completed and reviewed"
    
    echo "Review approved. Ready for CI/CD."
else
    # Request changes
    bd update "$review_id" --notes "Changes requested: [list of issues]"
    bd update "$original_issue" --status open --assignee "$new_dev_agent"
    bd update "$original_issue" --notes "Review feedback: [specific concerns]"
    
    echo "Changes requested. Reassigned to developer."
fi
```

#### 5. Update CI/CD Workflow

Modify the GitHub Actions workflow to only run on orchestrator-approved merges:

```yaml
name: Beads CI/CD with Review Enforcement

on:
  push:
    branches: [main]

jobs:
  verify-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Install beads
        run: |
          curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Verify review approval
        id: verify
        run: |
          bd sync
          
          # Extract issue IDs from commits
          issue_ids=$(git log -1 --pretty=%B | grep -oP 'bd-[a-f0-9]{4,6}(?:\.\d+)?' || echo "")
          
          if [ -z "$issue_ids" ]; then
            echo "No beads issues referenced in commit"
            exit 1
          fi
          
          # Check each issue has an approved review
          for issue_id in $issue_ids; do
            echo "Checking review status for $issue_id"
            
            # Find associated review issue
            review_issue=$(bd list --title-contains "Review:" --status closed --json | \
              jq -r ".[] | select(.description | contains(\"$issue_id\")) | select(.close_reason | contains(\"Approved\")) | .id" | head -1)
            
            if [ -z "$review_issue" ]; then
              echo "ERROR: No approved review found for $issue_id"
              echo "Policy violation: Code must be reviewed by different agent before merge"
              exit 1
            fi
            
            # Verify reviewer is different from developer
            dev_agent=$(bd show "$issue_id" --json | jq -r '.assignee')
            review_agent=$(bd show "$review_issue" --json | jq -r '.assignee')
            
            if [ "$dev_agent" = "$review_agent" ]; then
              echo "ERROR: Policy violation - same agent cannot develop and review"
              exit 1
            fi
            
            echo "✓ Issue $issue_id reviewed by $review_agent (developer: $dev_agent)"
          done
          
          echo "All issues have approved reviews from different agents"
      
      - name: Run CI/CD
        if: steps.verify.outcome == 'success'
        run: |
          # Your normal CI/CD steps here
          npm test
          npm run build
          npm run lint
```

### Orchestrator Configuration

Add to `.beads/config.yaml`:

```yaml
orchestration:
  enabled: true
  
  # Agent pools
  developer_agents:
    - dev-agent-1
    - dev-agent-2
    - dev-agent-3
  
  reviewer_agents:
    - review-agent-1
    - review-agent-2
  
  # Policy enforcement
  policies:
    separate_review: true          # Reviewer must differ from developer
    required_reviewers: 1           # Minimum reviewers per issue
    auto_assign: true              # Orchestrator auto-assigns work
    
  # Assignment strategy
  assignment:
    strategy: round_robin          # Options: round_robin, load_balanced, random
    max_concurrent_per_agent: 3    # Max issues per agent
```

### Policy Enforcement Examples

**Example 1: Simple orchestrator check**

```bash
# Get developer who worked on issue
dev_agent=$(bd show bd-a1b2 --json | jq -r '.assignee')

# Try to assign review to same agent (SHOULD FAIL)
bd create "Review bd-a1b2" --assignee "$dev_agent" -l review

# Orchestrator should reject this and select different agent
```

**Example 2: Pre-merge hook**

Create `.git/hooks/pre-push` to verify reviews before allowing push.

## Critical Configuration

### Custom Issue ID Patterns

**IMPORTANT:** The default issue pattern is `bd-[a-f0-9]{4,6}(?:\.\d+)?` which matches beads' hash-based IDs like `bd-a1b2` or `bd-f14c.3`.

**If your team uses custom ID formats** (e.g., `agent-gbv.11`, `task-abc.5`), you MUST configure the pattern:

#### Method 1: GitHub Repository Variables (Recommended)

1. Go to repository Settings → Secrets and variables → Actions → Variables
2. Click "New repository variable"
3. Add:
   - Name: `BEADS_ISSUE_PATTERN`
   - Value: `agent-\w+(?:\.\d+)?` (or your custom pattern)
4. Also add:
   - Name: `BEADS_VERSION`
   - Value: `0.29.0` (pin to specific version)
   - Name: `BEADS_METADATA_BRANCH`
   - Value: `beads-metadata` (if using protected branches)

#### Method 2: Environment Variables in Agent Scripts

Add to all agent scripts (orchestrator, developer, reviewer):

```bash
export BEADS_ISSUE_PATTERN='agent-\w+(?:\.\d+)?'
export BEADS_VERSION='0.29.0'
```

#### Method 3: Hardcode in Workflow (Not Recommended)

Edit the GitHub Actions workflow directly:

```yaml
env:
  ISSUE_PATTERN: 'agent-\w+(?:\.\d+)?'
  BEADS_VERSION: '0.29.0'
```

### Three Critical Fixes Implemented

This guide addresses three critical issues identified in initial review:

#### 1. ✅ Configurable Issue ID Regex

**Problem:** Hardcoded pattern `bd-[a-f0-9]{4,6}` doesn't match custom formats like `agent-gbv.11`

**Solution:** All scripts now use `${BEADS_ISSUE_PATTERN:-default}` with fallback:
- GitHub Actions: Reads from repository variables
- Orchestrator: Uses environment variable
- Agent scripts: Uses environment variable

**Example patterns:**
- Default beads: `bd-[a-f0-9]{4,6}(?:\.\d+)?`
- Custom agent: `agent-\w+(?:\.\d+)?`  
- Custom task: `task-[a-z0-9]+(?:\.\d+)?`
- Jira-style: `[A-Z]+-\d+`

#### 2. ✅ Protected Branch Support

**Problem:** CI pushing directly to `main` fails if branch is protected

**Solution:** New commit step detects protection and auto-switches to metadata branch:
```yaml
- name: Commit and push beads changes
  env:
    BEADS_BRANCH: ${{ vars.BEADS_METADATA_BRANCH || 'beads-metadata' }}
  run: |
    # Try main branch first
    if ! git push origin main 2>&1 | tee /tmp/push.log; then
      # Detected protection - use metadata branch
      if grep -q "protected branch" /tmp/push.log; then
        git checkout -b "$BEADS_BRANCH"
        git push origin "$BEADS_BRANCH"
      fi
    fi
```

#### 3. ✅ Pinned Beads Version

**Problem:** Using `main` branch for install causes reproducibility issues

**Solution:** Version now pinned via variable:
```yaml
- name: Install beads
  env:
    BEADS_VERSION: "0.29.0"  # UPDATE THIS when upgrading
  run: |
    curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/v${BEADS_VERSION}/scripts/install.sh | bash
    bd --version  # Verify
```

**To upgrade:** Update `BEADS_VERSION` variable in repository settings or workflow file.

## Advanced Configuration

### Protected Branches

If your `main` branch is protected and requires PRs:

```bash
# Initialize with separate metadata branch
bd init --branch beads-metadata
```

Then update the workflow to push to the metadata branch:

```yaml
- name: Commit beads changes
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    
    if [ -n "$(git status --porcelain .beads/)" ]; then
      git fetch origin beads-metadata
      git checkout beads-metadata
      git add .beads/
      git commit -m "beads: auto-update issues"
      git push origin beads-metadata
      git checkout main
    fi
```

### Custom Failure Handlers

Add custom logic for different failure types:

```yaml
- name: Create issue on test failure
  if: steps.tests.outcome == 'failure'
  run: |
    bd create "Test Failure on main" \
      -t bug -p 0 \
      -l "tests,ci-failure" \
      -d "Test suite failed. Review logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"

- name: Create issue on build failure
  if: steps.build.outcome == 'failure'
  run: |
    bd create "Build Failure on main" \
      -t bug -p 0 \
      -l "build,ci-failure" \
      -d "Build failed. Review logs: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
```

### Email Notifications

Add notifications for critical failures:

```yaml
- name: Notify on failure
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.MAIL_USERNAME }}
    password: ${{ secrets.MAIL_PASSWORD }}
    subject: CI/CD Failure - New Beads Issue Created
    body: |
      CI/CD pipeline failed on main branch.
      
      A new beads issue has been created automatically.
      Check the repository for details: ${{ github.server_url }}/${{ github.repository }}
    to: team@example.com
    from: ci-bot@example.com
```

## Troubleshooting

### Issue: CI/CD can't push changes

**Symptom:** GitHub Actions fails with "permission denied" when pushing beads changes.

**Solution:** Add write permissions to the workflow:

```yaml
permissions:
  contents: write

jobs:
  ci-with-beads:
    runs-on: ubuntu-latest
    # ... rest of job
```

### Issue: Issues not closing automatically

**Symptom:** Issues referenced in commits aren't being closed.

**Solutions:**
1. Verify issue IDs are in commit messages: `bd-a1b2` format
2. Check the extraction script matched the IDs: view workflow logs
3. Ensure `bd close` command succeeded: check for error output
4. Verify git push succeeded: check workflow completion

### Issue: Merge conflicts in .beads/ directory

**Symptom:** Git merge conflicts in `.beads/beads.jsonl`.

**Solution:** Beads has a custom merge driver that should handle this automatically. If not configured:

```bash
git config merge.beads.driver "bd merge %A %O %A %B"
git config merge.beads.name "bd JSONL merge driver"
echo ".beads/beads.jsonl merge=beads" >> .gitattributes
```

### Issue: Database out of sync

**Symptom:** Local beads database doesn't match remote.

**Solution:**

```bash
bd sync        # Force sync
bd import      # Re-import from JSONL if needed
```

## Best Practices

### For AI Agents

1. **Always sync first**: Run `bd sync` after `git pull`
2. **Reference issues**: Include beads IDs in all relevant commits
3. **Update status**: Keep issue status current (`in_progress`, etc.)
4. **Close completed work**: Don't rely solely on CI/CD auto-close
5. **File discovered issues**: Use `bd create` for bugs found during work
6. **Link dependencies**: Use `bd dep add` to track relationships

### For Teams

1. **Consistent naming**: Use standard labels (`ci-failure`, `automated`)
2. **Priority levels**: Agree on priority meanings (0=critical, 1=high, etc.)
3. **Review automation**: Periodically check auto-created issues
4. **Clean up old issues**: Use `bd compact` for old closed issues
5. **Document workflows**: Keep this guide updated with team practices

### For Repository Maintainers

1. **Initialize properly**: Use `bd init --quiet` for automated setups
2. **Commit .beads/**: Include beads JSONL files in git
3. **Ignore database**: Add `.beads/*.db` to `.gitignore`
4. **Test workflows**: Verify CI/CD automation before production use
5. **Monitor failures**: Review auto-created issues regularly

## FAQ

**Q: Should I use the Node.js or Python workflow examples?**  
A: Use the workflow that matches your project's language. The concepts are identical - only the tool commands differ. If you have both Node and Python in a monorepo, run both workflows or combine them into a single workflow.

**Q: Can I mix pre-commit frameworks (Husky for Node, pre-commit for Python)?**  
A: Yes! In a monorepo, you can use Husky for Node code and `.pre-commit-config.yaml` for Python. Just ensure both are configured with `stages: [commit]` or CI skip headers.

**Q: Can multiple agents work on different issues simultaneously?**  
A: Yes! Beads uses hash-based IDs to prevent collisions. Each agent's changes sync via git.

**Q: What happens if CI/CD creates an issue but someone already fixed it?**  
A: The issue will exist but can be immediately closed. Consider adding deduplication logic if this happens frequently.

**Q: Do I need to run `bd sync` manually?**  
A: No, beads auto-syncs on most operations. Manual `bd sync` is only needed if you want to force an immediate sync.

**Q: Can I use this with protected branches?**  
A: Yes! Use `bd init --branch beads-metadata` to commit beads changes to a separate branch. See "Protected Branches" section above.

**Q: What if CI/CD fails due to infrastructure issues, not code?**  
A: The auto-created issue will have full context. Review the logs and close the issue if it's not code-related, or create a separate infrastructure issue.

**Q: How do I prevent CI/CD from creating duplicate issues?**  
A: Add deduplication logic that checks for existing open issues with the same title or labels before creating a new one.

## Additional Resources

- **Beads Documentation**: https://github.com/steveyegge/beads
- **Beads Quickstart**: `bd quickstart` (interactive tutorial)
- **GitHub Actions Docs**: https://docs.github.com/actions
- **Issue Tracking Best Practices**: See `docs/LABELS.md` in beads repo

## Support

For issues with this integration:
1. Check workflow logs in GitHub Actions
2. Verify beads installation: `bd info`
3. Test locally: `bd create "test" && bd list`
4. Review beads issues: https://github.com/steveyegge/beads/issues

---

**Version:** 2.1 ✨  
**Last Updated:** 2025-02-14  

**Changes in v2.1:**  
- ✅ Safe deployment implementation order (6-step rollout)
- ✅ Parallel run strategy for workflow validation
- ✅ Python/pytest/ruff examples alongside Node.js
- ✅ Complete workflow behavior matrix (pre-commit/PR/post-merge)
- ✅ Language-specific notes and comparison table

**Changes in v2.0:**  
- ✅ Configurable issue ID regex patterns  
- ✅ Protected branch auto-detection and handling  
- ✅ Pinned beads version for reproducibility  
- ✅ Complete multi-agent orchestration with review enforcement  

**Maintained by:** [Your Team Name]
