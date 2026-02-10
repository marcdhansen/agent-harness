# Task: Mandate Full SOP for SOP Infrastructure Code Changes (agent-harness-7sy)

## Objective

Enforce the full SOP process (feature branch, PR, code review) for any code changes to SOP infrastructure, closing a gap in the current `sop-modification` skill.

## Implementation Details

### 1. Detection Logic

Added `check_sop_infrastructure_changes()` to `check_protocol_compliance.py` which detects changes to:

- Orchestrator scripts
- Skill scripts
- SKILL.md files
- SOP documentation in `.agent/docs/`

### 2. Escalation Trigger

Updated `run_turbo_initialization()` to call the detection logic. If SOP infrastructure changes are detected:

- Turbo Mode is blocked
- Full Mode escalation is required (--init)

### 3. Documentation

- Updated `sop-modification/SKILL.md` to expand its scope to SOP infrastructure code changes.
- Updated `SOP_COMPLIANCE_CHECKLIST.md` Phase 4 Execution section to document the escalation trigger.

### 4. Verification

Created `tests/test_sop_infrastructure_escalation.py` with 7 test cases covering:

- No changes (no escalation)
- Orchestrator script changes (escalation)
- Skill script changes (escalation)
- SKILL.md changes (escalation)
- SOP doc changes (escalation)
- Regular code changes (no escalation)
- Mixed changes (escalation)

All tests PASSED.

## Status: COMPLETED

## Approval

👍 APPROVED FOR EXECUTION (User: Marc Hansen, 2026-02-10 16:00)
- [x] Plan Approved (User: Marc Hansen, 2026-02-10 16:00)
