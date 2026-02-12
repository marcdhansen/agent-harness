# Implementation Plan - Automated Local Branch Pruning (agent-harness-ua6)

## Problem

The current Finalization protocol requires branches to be clean and pushed but does not enforce local cleanup of merged branches. This has led to an accumulation of stale local branches.

## Proposed Changes

1. **Implement Pruning Logic**: Create a function to identify and delete local branches that have been fully merged into the main branch.
2. **Update Orchestrator**: Modify `check_protocol_compliance.py` (specifically the finalization validator) to verify that no stale local branches remain.
3. **Safety Checks**: Ensure strict safety to prevent deletion of unmerged work or the current branch.

## Verification Plan

1. **Unit Tests**: Test the pruning logic with mocked git responses.
2. **Integration Test**: Create a temporary git repo, create branches, merge them, and verify the pruner deletes them.
3. **Orchestrator Check**: Verify the `check_protocol_compliance.py` correctly fails if stale branches exist and passes after cleanup.

## Tasks

- [ ] Create `branch_pruner.py` module (or add to `git_validator.py`)
- [ ] Implement `prune_merged_branches` function
- [ ] Add `check_local_branch_cleanup` validator to Orchestrator
- [ ] Verify with tests
