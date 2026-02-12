# Task: agent-harness-3fd - Enforce Branch-Issue Coupling and Started State in Orchestrator

## Status

- [x] Research current implementation and identify "holes"
- [x] Create reproduction tests
- [x] Harden `check_branch_issue_coupling` and `check_beads_issue`
- [x] Ensure enforcement across all relevant phases (Initialization, Execution, Finalization)
- [x] Verify fix with tests
- [x] Capture results and close

## Implementation Plan

### 1. Research & Analysis

- [x] Read `check_protocol_compliance.py` and its validators.
- [x] Identify discrepancy between `check_branch_issue_coupling` and `check_beads_issue`.
- [x] Identify "Turbo Mode" hole (Turbo doesn't check coupling).

### 2. Implementation

- [x] Update `get_active_issue_id` to be stricter.
- [x] Update `check_branch_issue_coupling` to not skip silently on non-feature branches if work is detected.
- [x] Update `check_beads_issue` to ensure consistency.
- [x] Add coupling check to Turbo Initialization if possible (as a warning).

### 3. Verification

- [x] Run `pytest tests/test_branch_issue_coupling.py` (to be created).
- [x] Run `check_protocol_compliance.py --status`.

## Approval

(Approval cleared)
