# Walkthrough - Hardening Branch-Issue Coupling and Started State

This walkthrough documents the hardening of the Orchestrator's branch-issue coupling and started state enforcement.

## Problem Statement

The Orchestrator previously had potential gaps where:

1. Feature branches not follow naming conventions could bypass coupling checks.
2. `get_active_issue_id` could fall back to `bd ready` even on feature branches, potentially linking the session to an unrelated ready issue.
3. Turbo Mode initialization did not check for branch-issue coupling, allowing protocol bypass for certain tasks.

## Changes Implemented

### 1. Hardened `get_active_issue_id`

- Modified `validators/git_validator.py` to strictly derive the active issue ID from the branch name when on a feature branch.
- Removed fallback to `bd ready` for all branches except protected base branches (`main`, `master`, `develop`).
- This ensures that on any feature branch, the active issue is EXCLUSIVELY the one specified in the branch name.

### 2. Hardened `check_branch_issue_coupling`

- Updated to block any branch that does not follow the `agent/issue-id` (or similar) convention, unless it is a protected base branch.
- Enforced that feature branches MUST be coupled to a 'started' Beads issue.
- Added explicit reporting of protocol violations for non-standard branch names.

### 3. Hardened Turbo Mode Initialization

- Added `check_branch_issue_coupling` as a MANDATORY blocker in Turbo Mode initialization.
- This prevents starting any work (even metadata-only) on misnamed or unstarted branches, enforcing the "One task per agent, branch isolation" rule from the very start.

## Verification Results

### Automated Tests

- Created `tests/repro_issue_coupling.py` and `tests/test_hardened_coupling.py`.
- Verified that `get_active_issue_id` no longer falls back to `bd ready` on generic branches.
- Verified that `check_branch_issue_coupling` blocks non-standard branch names.
- Verified that the check passes on `main` (for discovery/planning) but requires `status:started` on feature branches.

### Manual Verification

- Verified that `--init` fails on a branch named `test-failure`.
- Verified that `--init` passes on `agent/agent-harness-3fd` once the issue is started.

## Impact

- **Security/Protocol**: Significantly reduced the risk of multi-issue pollution and SOP bypass.
- **Developer Experience**: Clearer error messages when branch naming or state conventions are violated.
