# 📋 Implementation Plan: agent-harness-gf6 - Implement bd note alias and automated debrief-to-beads comment injection

## Objective

Reduce cognitive load and improve documentation by automating the synchronization of session debriefs to Beads issue comments and providing a 'bd note' alias for manual notes.

## Proposed Changes

### 1. New Validator: `inject_debrief_to_beads` (`src/agent_harness/compliance.py`)

- Implement a new validator `inject_debrief_to_beads` that:
  - Identifies the active Beads issue ID.
  - Reads the most recent `debrief.md` from the brain directory.
  - Extracts the "Implementation Details" or the entire content if preferred.
  - Sanitizes the content for shell execution.
  - Checks if the debrief has already been injected (to avoid duplicates).
  - Calls `bd comments add <issue-id> -f <path-to-debrief>` or pipes the content if a temporary file is needed.
- **Improved Messaging**: Confirm injection or explain why it was skipped.

### 2. Update Checklist (`.agent/rules/checklists/retrospective.json`)

- Add `inject_debrief_to_beads` as a step in the Retrospective phase.
- Mark it as a `WARNING` or `BLOCKER` depending on desired strictness (initially `WARNING` recommended to ensure it doesn't block finalization if `bd` fails).

### 3. Register Validator (`src/agent_harness/nodes/finalization.py`)

- Register the new validator in the `retrospective_node`.

### 4. Provide Alias (Documentation)

- Since `bd` is a binary, we will document the alias for user shells: `alias bd-note='bd comments add'`.
- Optionally, we could provide a wrapper script in `.agent/bin/bd-note` if persistent shell aliases are difficult to manage across different environments.

### 5. Testing (`tests/test_debrief_injection.py`)

- Mock `bd show` and `bd comments add`.
- Verify extraction logic from `debrief.md`.
- Verify duplicate prevention logic.

## Verification

### Automated

- `pytest tests/test_debrief_injection.py`

### Manual

- Run a session, complete work, and run finalization.
- Verify the debrief content appears in `bd show <issue-id>`.

## Blast Radius

- **Low**: This is an additive feature in the Retrospective phase. If it fails, it should ideally just warn rather than block the entire session closure (if configured as a warning).

## Rollback Plan

- Remove the validator from `retrospective.json` and `finalization.py`.
