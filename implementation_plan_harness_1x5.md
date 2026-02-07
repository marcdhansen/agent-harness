# Implementation Plan - agent-harness-1x5: Protocol Compliance Verification in Session Summaries

This plan outlines the steps to include Protocol Compliance verification in session summaries and handoffs, ensuring that agents explicitly confirm SOP compliance at the end of each session.

## User Review Required

> [!IMPORTANT]
> This change modifies the mandatory SOP requirements for session closure (Phase 6: Retrospective). Agents will now be required to include a Protocol Compliance summary in their final handoffs.

- **Objective**: Integrate Orchestrator-validated compliance status into session summaries and handoffs.
- **Scope**: SOP documentation (`06_retrospective.md`, `SOP_COMPLIANCE_CHECKLIST.md`) and the Orchestrator script.

## Proposed Changes

### 1. SOP Documentation Updates

#### `~/.agent/docs/phases/06_retrospective.md`

- Add "Protocol Compliance Verification" to the `Handoff Summary` checklist.
- Specify that the summary must include the outcome of `check_protocol_compliance.py --retrospective`.

#### `~/.agent/docs/SOP_COMPLIANCE_CHECKLIST.md`

- Update Phase 6 checklist to include Protocol Compliance verification.

### 2. Orchestrator Enhancement

#### `~/.gemini/antigravity/skills/Orchestrator/scripts/check_protocol_compliance.py`

- Enhance `run_retrospective` and `run_status` to provide a concise, copy-pasteable "SOP Compliance Summary".
- Add a new `--summary` flag that outputs ONLY the compliance summary for inclusion in reports.

## Verification Plan

### Automated Tests

- Run `python check_protocol_compliance.py --status` and verify new output format.
- Run `python check_protocol_compliance.py --summary` and verify concise output.

### Manual Verification

- Perform a dummy session lifecycle and verify that the Retrospective phase requirements are clear and achievable.
- Check that the Orchestrator correctly identifies missing compliance information if it were to be added as a check (future enhancement).

## Deployment Steps

1. Update SOP documentation files.
2. Modify Orchestrator Python script.
3. Verify changes locally.
4. Commit and push changes.
