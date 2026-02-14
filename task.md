# Task: agent-2zl - Allow flexible branch naming and project IDs

## Objective

The git_validator.py and other compliance checks strictly enforce 'agent-harness' prefix in several places. Generalize these to support various project prefixes.

## Tasks

- [x] Generalize `check_branch_info` in global orchestrator
- [x] Generalize `get_active_issue_id` regex in global orchestrator
- [x] Generalize prune and closed issue checks in global orchestrator
- [x] Sycn changes to local `src/agent_harness/compliance.py`
- [x] Add comprehensive tests for flexible ID detection
- [x] Verify all tests pass

## Approval

👍 APPROVED by Antigravity (Local context)
