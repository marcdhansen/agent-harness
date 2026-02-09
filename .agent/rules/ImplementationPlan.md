# 📋 Implementation Plan: agent-harness-v0o - Enforce Rebase-Squash Strategy

## Objective

Prevent SOP violations (merge commits/multi-commit PRs) by automating enforcement in the Orchestrator's Finalization phase.

## Proposed Changes

### 1. Orchestrator Enhancement (`check_protocol_compliance.py`)

- **`validate_atomic_commits()`**:
  - Update logic to compare current branch against `main`.
  - Count commits: `git rev-list --count main..HEAD`.
  - If count > 1, block finalization with a clear instruction to squash.
  - Check for merge commits: `git rev-list --merges main..HEAD`.
  - If any merge commits found, block finalization.
- **Improved Messaging**:
  - Provide specific git commands for the user/agent to fix the violation (e.g., `git rebase -i main`).

### 2. Testing (`tests/test_orchestrator_atomic_commits.py`)

- Implement 5 distinct test cases:
  1. **Success**: Single commit, no merges.
  2. **Failure**: Multiple commits (no merges).
  3. **Failure**: Single commit that is a merge commit.
  4. **Failure**: Multiple commits including a merge commit.
  5. **Success**: Rebased and squashed branch (1 commit).

### 3. Browser Automation (`skills/browser-manager/`)

- Review and update Playwright scripts to ensure the "Squash and merge" button is explicitly targeted by ID or label, rather than relying on default browser state.

### 4. PR Template Updates

- Add a mandatory checklist item in `.github/PULL_REQUEST_TEMPLATE.md`:
  - `[ ] Branch has been squashed into a single atomic commit.`
  - `[ ] No merge commits are present (rebase used instead).`

## Verification

### Automated

- `pytest tests/test_orchestrator_atomic_commits.py`
- `pytest tests/test_orchestrator.py` (ensure no regressions)

### Manual

- Create a branch with 2 commits and try to run `check_protocol_compliance.py --finalize`. Verify it blocks.
- Squash the commits and verify it passes.

## Blast Radius

- **Low-Medium**: Only affects the Finalization phase. If logic is too strict or buggy, it could block PR creation.
- **Dependencies**: Depends on `git` CLI availability.

## Rollback Plan

- Revert changes to `check_protocol_compliance.py`.
