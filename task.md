# Task: Modify SOP to require Beads Issue Identifier in summaries and hand-offs [agent-harness-iiy]

## Objectives

- [x] Implement `check_handoff_beads_id` validator <!-- id: 0 -->
- [x] Register validator in `finalization` and `retrospective` nodes <!-- id: 1 -->
- [x] Add unit tests for `check_handoff_beads_id` <!-- id: 2 -->
- [x] Verify integrated checklist requirement <!-- id: 3 -->

## Approval

[ ] Protocol Compliance Verified

## Implementation Details

- Added `check_handoff_beads_id` to `src/agent_harness/compliance.py`.
- Registered validator in `finalization_node` and `retrospective_node`.
- Updated `.agent/rules/checklists/retrospective.json` (already present on branch).
