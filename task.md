# Task: Prevent Orphaned Pull Requests and Workspace Drift [agent-harness-niy]

## Objectives

- [x] Implement `check_handoff_pr_verification` validator
- [x] Implement `check_beads_pr_sync` validator
- [x] Implement `check_workspace_cleanup` validator
- [x] Update SOP documentation for PR supersession
- [x] Integrate all gates into Orchestrator finalization

## Approval

[ ] Protocol Compliance Verified

## Implementation Details

- Added validators to `finalization_validator.py`
- Updated JSON checklists in `.agent/rules/checklists/`
- Verified with unit tests in `tests/test_handoff_pr_verification.py`
- Resolved merge conflicts with `main` (harness-4cq).
