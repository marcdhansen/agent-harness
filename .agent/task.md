# Task: agent-harness-v0o - Enforce Rebase-Squash Strategy in PR Workflow

## Objective

Enforce the rebase-squash strategy by updating the Orchestrator to block PRs with multiple commits or merge commits. This ensures a clean, linear history with atomic commits for every feature merged into `main`.

## Roadmap

- [x] Phase 1: Planning & Initialization
  - [x] Create feature branch `agent/agent-harness-v0o`
  - [x] Establish implementation plan
  - [x] Get plan approval
- [x] Phase 2: Orchestrator Enhancement
  - [x] Update `validate_atomic_commits()` in `check_protocol_compliance.py`
  - [x] Implement detection for merge commits (e.g., `git log --merges`)
  - [x] Implement detection for multiple commits on feature branch relative to `main`
- [x] Phase 3: Testing & Verification
  - [x] Create/Update `tests/test_orchestrator_atomic_commits.py`
  - [x] Implement 6 test cases for atomic commits
  - [x] Verify enforcement blocks non-compliant PRs
- [x] Phase 4: Browser Automation & Documentation
  - [x] Update PR template with pre-merge checklist (previously existing, verified)
  - [x] Enhance browser automation guidance for "Squash and merge"
  - [x] Update SOP documentation (`git-workflow.md` and `SKILL.md`)
- [x] Phase 5: Finalization
  - [x] Verify everything with all tests passing
  - [x] Create PR and complete session
    - PR Workspace: <https://github.com/marcdhansen/agent-harness/pull/6>
    - PR dot-gemini: <https://github.com/marcdhansen/dot-gemini/pull/7>
    - PR dot-agent: <https://github.com/marcdhansen/dot-agent/pull/5>
    - Review Issue: agent-harness-6fn (P0)

## Plan Status

- [x] Implementation Complete
- [x] PR Submitted & Review Issue Created
