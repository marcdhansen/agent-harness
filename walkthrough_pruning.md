# Walkthrough: Implementing Automated Local Branch Pruning

## Summary

To prevent the accumulation of stale local branches, we implemented an automated check within the Finalization protocol. This new validation logic detects merged branches that haven't been deleted locally and blocks finalization until they are cleaned up (via `--clean` or manual deletion).

## Changes

### 1. Updated `prune_local_branches` in `git_validator.py`

- Added `dry_run` parameter (default: `False`).
- When `dry_run=True`, logical check only: identifies branches that would be pruned and returns validation failure if any exist.
- When `dry_run=False` (default), performs actual deletion (`git branch -d`).

### 2. Updated `Finalization` Phase in `check_protocol_compliance.py`

- Added a call to `prune_local_branches(dry_run=True)` before workspace cleanup check.
- This ensures that users cannot finalize a session if they have stale branches hanging around.

### 3. Updated Tests

- Added test coverage in `tests/test_orchestrator.py` `TestOrchestratorFinalization`.
- Mocked dependencies to ensure robust testing without external side effects (gh/beads calls).

## Verification

- Ran `python -m unittest tests.test_orchestrator.TestOrchestratorFinalization` successfully.
- Verified that `run_clean_state` (legacy cleanup) continues to work as expected (invoking pruning).

## Next Steps

- Merge this PR.
- Observing if "Stale Branches" check catches future leaks.
