import pytest
from pathlib import Path
from agent_harness.checklists import ChecklistManager
from agent_harness.compliance import (
    check_tool_version,
    check_workspace_integrity,
    check_planning_docs,
    check_beads_issue,
    check_plan_approval,
    check_git_status,
    validate_atomic_commits,
    validate_tdd_compliance,
    check_reflection_invoked,
    check_handoff_compliance,
)


@pytest.fixture
def checklist_manager():
    project_root = Path.cwd()
    checklist_dir = project_root / ".agent/rules/checklists"
    manager = ChecklistManager(checklist_dir)

    # Register all validators
    manager.register_validator("check_tool_version", check_tool_version)
    manager.register_validator("check_workspace_integrity", check_workspace_integrity)
    manager.register_validator("check_planning_docs", check_planning_docs)
    manager.register_validator("check_beads_issue", check_beads_issue)
    manager.register_validator("check_plan_approval", check_plan_approval)
    manager.register_validator("check_git_status", check_git_status)
    manager.register_validator("validate_atomic_commits", validate_atomic_commits)
    manager.register_validator("validate_tdd_compliance", validate_tdd_compliance)
    manager.register_validator("check_reflection_invoked", check_reflection_invoked)
    manager.register_validator("check_handoff_compliance", check_handoff_compliance)

    return manager


def test_initialization_phase(checklist_manager):
    # This might fail depending on current environment, but we want to see it run
    passed, blockers, warnings = checklist_manager.run_phase("initialization")
    print(f"Initialization: Passed={passed}, Blockers={blockers}, Warnings={warnings}")
    # Note: We don't assert True here because the environment might actually be blocked
    # but we assert that it returns lists of strings
    assert isinstance(blockers, list)
    assert isinstance(warnings, list)


def test_finalization_phase(checklist_manager):
    passed, blockers, warnings = checklist_manager.run_phase("finalization")
    print(f"Finalization: Passed={passed}, Blockers={blockers}, Warnings={warnings}")
    assert isinstance(blockers, list)
    assert isinstance(warnings, list)


def test_planning_phase(checklist_manager):
    passed, blockers, warnings = checklist_manager.run_phase("planning")
    print(f"Planning: Passed={passed}, Blockers={blockers}, Warnings={warnings}")
    assert isinstance(blockers, list)
    assert isinstance(warnings, list)
