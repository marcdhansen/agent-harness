# 📋 Implementation Plan: agent-harness-1wj - PR Workflow + Handoff Updates

## Objective

Modify SOP to require all code changes via PRs. Update Finalization phase to create PRs, update Handoff Protocol, and enforce PR review/approval.

## Proposed Changes

### 1. SOP Documentation Updates

- **`AGENTS.md`**:
  - Mandate that all code changes Must happen on feature branches and be merged via PRs.
  - Explicitly state that PR approval from a different agent is blocking for implementation tasks.
- **`.agent/docs/phases/05_finalization.md`**:
  - Add requirement to create a PR before closing the session.
  - Provide instructions on using `gh pr create` or asking the user to create one.
- **`.agent/docs/phases/06_retrospective.md`**:
  - Update the Handoff section to mandate providing the PR link.
- **`SOP_COMPLIANCE_CHECKLIST.md`**:
  - Add checkboxes for "PR Created" in Phase 5 and "PR Link in Handoff" in Phase 6.

### 2. Orchestrator Enhancement (`check_protocol_compliance.py`)

- **Initialization Check**:
  - No changes needed (already checks for feature branch if implementing).
- **Finalization Check (`--finalize`)**:
  - Add a check to verify if a PR exists for the current branch using `gh pr list --head <branch>`.
  - If no PR exists, block finalization (unless in Turbo Mode).
- **Retrospective Check (`--retrospective`)**:
  - Add a check to verify that the handoff message or a handoff file contains a valid GitHub PR URL.

## Verification

### Manual Verification

1. Create a dummy test branch.
2. Attempt to run `--finalize` without a PR; verify it blocks.
3. Create a PR for the branch.
4. Run `--finalize` again; verify it passes.
5. Create a handoff without a PR link; verify `--retrospective` fails.
6. Add PR link to handoff; verify it passes.

### Automated Verification

- Update `tests/test_orchestrator.py` to include tests for the new PR-related checks.

## Blast Radius

- **Medium**: This change modifies the core development workflow for all agents. Failure in the Orchestrator check could block all progress until fixed.
- **Dependencies**: Requires `gh` CLI to be installed and authenticated for automated PR detection.

## Rollback Plan

- Revert changes to `AGENTS.md` and Orchestrator script.
