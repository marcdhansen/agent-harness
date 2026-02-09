# Task: agent-harness-1wj - PR Workflow + Handoff Updates

## Objective

Modify SOP to require all code changes via PRs. Update Finalization phase to create PRs instead of direct merge. Update Handoff Protocol to include PR link. Add Turbo Mode exception for admin-only changes. Prevent self-review. PR approval is blocking.

## Roadmap

- [x] Phase 1: Planning & Initialization
  - [x] Create feature branch `agent/agent-harness-1wj`
  - [x] Create progress log
  - [x] Establish implementation plan
  - [x] Get plan approval
- [x] Phase 2: Implementation (SOP Updates)
  - [x] Update `AGENTS.md` with PR workflow rules
  - [x] Update `.agent/docs/phases/05_finalization.md`
  - [x] Update `.agent/docs/phases/06_retrospective.md`
  - [x] Update `SOP_COMPLIANCE_CHECKLIST.md`
- [x] Phase 3: Orchestrator Enhancement
  - [x] Implement PR existence check in `check_protocol_compliance.py --finalize`
  - [x] Implement Handoff PR link check in `check_protocol_compliance.py --retrospective`
- [x] Phase 4: Verification & Finalization
  - [x] Verify enforcement with tests/manual runs
  - [x] Create PR for this task
  - [x] Full SOP Finalization

## Plan Status

- [x] Plan completed and approved
