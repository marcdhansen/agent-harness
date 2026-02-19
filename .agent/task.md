# Task: agent-rgi - Fix PR Merge → Beads Issue Auto-Close Gap

## Objective

Fix the gap where CI/CD fails to close beads issues on PR merge due to missing database, but errors are suppressed. Issues remain open indefinitely.

## Problem

- CI workflow tries to close beads issues on merge but fails silently
- Issues remain open in beads indefinitely
- No verification required in SOP

## Solution: Hybrid Fix

### Part 1: CI Workflow Fix
- Updated `.github/workflows/post-merge-ci.yml`:
  - Pinned beads to v0.50.3 (supports JSONL mode)
  - Added proper error handling and logging
  - CI now attempts to close issues with clear warnings on failure

### Part 2: SOP Updates
- `SOP_COMPLIANCE_CHECKLIST.md`: Changed "optional" to MANDATORY verification
- `05_finalization.md`: Added explicit verification checklist item
- `SOP.md`: Updated automated closure section
- `HOW_TO_USE_BEADS.md`: Added verification requirements

## Verification

- ✅ CI executes close command successfully
- ✅ CI logs warnings when closure fails
- ✅ SOP requires manual verification (addresses beads limitations)
- ✅ Test issue agent-pkb closed manually

## Todos

- [x] Create beads issue for tracking (agent-rgi)
- [x] Fix CI workflow - bd sync and close issues
- [x] Update SOP - make issue closure mandatory
- [x] Add test case - verify CI closes issue on merge
- [x] Run finalization

## Plan Approval

- [x] Plan approved by USER (in-session approval)
