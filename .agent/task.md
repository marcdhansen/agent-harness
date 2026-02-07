# Task: Enhance --init check with pre-flight validation (agent-harness-kxh)

## Objective

Further harden the Orchestrator by adding checks for tool versions and workspace integrity during the --init phase.

## Completion Status

- [x] Research current check implementation
- [x] Define required tool versions and workspace integrity criteria
- [x] Implement pre-flight validation logic in `check_protocol_compliance.py`
- [x] Add tool version checking (e.g., bd, uv, git)
- [x] Add workspace integrity checking (e.g., existence of .agent directory, beads db)
- [x] Verify validation failure cases
- [x] Update documentation

## Deliverables

- [x] Updated `check_protocol_compliance.py` with pre-flight validation
- [x] Updated documentation for Initialization phase
- [x] Test cases for pre-flight validation (`tests/test_preflight.py`)

## Approval

Approved

## Quality Results

- [x] TDD compliance verified
- [x] Tool version checks functional
- [x] Workspace integrity checks functional
