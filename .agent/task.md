# Task: agent-harness-6ec - Enforce Retrospective as strict BLOCKER

## Objective

Promote all retrospective checks to `BLOCKER` to ensure mandatory compliance with strategic learning and handoff documentation.

## Todos

- [x] Update `.agent/rules/checklists/retrospective.json` to promote warnings to blockers <!-- id: 0 -->
- [x] Verify `src/agent_harness/nodes/finalization.py` enforcement logic <!-- id: 1 -->
- [x] Create and run tests in `tests/test_retrospective_enforcement.py` <!-- id: 2 -->
- [x] Run full finalization check <!-- id: 3 -->

## Progress Log

### 2026-02-15

- Task started.
- Created implementation plan.
- Identified target files.
- Promoted `inject_debrief_to_beads` to `BLOCKER` in `retrospective.json`.
- Verified all retrospective checks are now blockers.
- Added unit tests to ensure enforcement.
- Verified orchestrator node logic.
🏁

## Plan Approval

- [x] Plan approved by USER <!-- id: approved -->
