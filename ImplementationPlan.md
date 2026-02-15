# Implementation Plan - Enforce Retrospective as strict BLOCKER (agent-harness-6ec)

## Problem

The Retrospective phase in the Orchestrator currently uses `WARNING` for several key checks (e.g., `inject_debrief_to_beads`). This allows agents to finalize sessions even if strategic learning and handoff documentation are incomplete. To maintain high-quality documentation and SOP compliance, all retrospective checks must be promoted to `BLOCKER`.

## Proposed Changes

### 1. Update Retrospective Checklist (`.agent/rules/checklists/retrospective.json`)

- Change `inject_debrief_to_beads` from `WARNING` to `BLOCKER`.
- Ensure all other checks in the `retrospective` phase are set to `BLOCKER`.

### 2. Verify Orchestrator Enforcement (`src/agent_harness/nodes/finalization.py`)

- Review `retrospective_node` to ensure it correctly transitions to `COMPLETE` only if `passed` is true (no blockers).
- Verify that the `ChecklistManager.run_phase` correctly identifies any `BLOCKER` failures as making `passed = False`.

### 3. Verification Plan

#### Automated Tests

- Create a new test file `tests/test_retrospective_enforcement.py` that:
  - Mocks the `ChecklistManager`.
  - Verifies that a failed `inject_debrief_to_beads` (now a blocker) results in `passed=False` and prevents session completion.
- Run `pytest tests/test_checklists.py` to ensure core checklist logic remains intact.

#### Manual Verification

- Run the orchestrator in a test environment.
- Intentionally fail a retrospective check (e.g., provide an invalid Beads ID in `debrief.md`).
- Verify that the orchestrator blocks finalization.

## Blast Radius Analysis

- **Low**: This change only affects the Retrospective phase of the Orchestrator. It does not touch core agent logic or tool execution.
- **Impact**: Any agent (including myself) will now be blocked if retrospective steps fail.

## Rollback Plan

- Revert the changes to `.agent/rules/checklists/retrospective.json` (change `BLOCKER` back to `WARNING`).
