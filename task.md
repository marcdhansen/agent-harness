# Task: Modify SOP to require 🏁 emoji for session wrap-up confirmation [agent-harness-b9y]

## Objectives

- [ ] Implement `check_wrapup_indicator_symmetry` validator <!-- id: 0 -->
- [ ] Implement `check_wrapup_exclusivity` validator <!-- id: 1 -->
- [ ] Update `finalization_debriefing.py` for automated 🏁 injection <!-- id: 2 -->
- [ ] Update retrospective checklist with new checks <!-- id: 3 -->
- [ ] Update Orchestrator to enforce 🏁 in session summary <!-- id: 4 -->
- [ ] Formalize 🏁 in SOP documentation (`AGENTS.md`) <!-- id: 5 -->

## Approval

[ ] Protocol Compliance Verified

## Implementation Details

- New validators in `src/agent_harness/compliance.py`.
- Automated injection in the debriefing script.
- Integration with Orchestrator's retrospective phase.
