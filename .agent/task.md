# Task: agent-rgi - Fix PR Merge → Beads Issue Auto-Close Gap

## Objective

Fix the gap where CI/CD fails to close beads issues on PR merge due to missing database, but errors are suppressed. Issues remain open indefinitely.

## Problem

- CI workflow tries to close beads issues on merge but fails silently
- Issues remain open in beads indefinitely
- No verification required in SOP

## Solution: Hybrid Fix

### Part 1: CI Workflow Fix (COMPLETED)
- Updated `.github/workflows/post-merge-ci.yml`:
  - Added `BD_ISSUE_PREFIX` env var to both sync and close steps
  - Removed faulty database check (lines 191-195) that always failed in --no-db mode
  - Added `--no-db` flag to `bd close` command
  - Added `--no-db` flag to final `bd sync` command

### Part 2: SOP Updates
- `SOP_COMPLIANCE_CHECKLIST.md`: Changed "optional" to MANDATORY verification
- `05_finalization.md`: Added explicit verification checklist item
- `SOP.md`: Updated automated closure section
- `HOW_TO_USE_BEADS.md`: Added verification requirements

## Verification

- ✅ CI executes close command with --no-db flag
- ✅ CI sets BD_ISSUE_PREFIX env var for JSONL-only mode
- ✅ Removed faulty database check that prevented closing
- ✅ SOP requires manual verification (addresses beads limitations)
- ✅ Test: Verified bd --no-db close works with BD_ISSUE_PREFIX

## Todos

- [x] Create beads issue for tracking (agent-rgi)
- [x] Fix CI workflow - bd sync and close issues
- [x] Update SOP - make issue closure mandatory
- [x] Add test case - verify CI closes issue on merge
- [x] Run finalization

## Plan Approval

- [x] Plan approved by USER (in-session approval)
