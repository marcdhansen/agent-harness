from datetime import datetime
from pathlib import Path

from agent_harness.compliance import (
    check_approval,
    check_tool_version,
    check_workspace_integrity,
    check_planning_docs,
    check_beads_issue,
    check_plan_approval,
)
from agent_harness.checklists import ChecklistManager
from agent_harness.state import ProtocolState


def initialization_node(state: ProtocolState) -> ProtocolState:
    """
    Node for performing the Initialization check using JSON checklists.
    """
    project_root = Path.cwd()
    checklist_dir = project_root / ".agent/rules/checklists"

    manager = ChecklistManager(checklist_dir)

    # Register validators
    manager.register_validator("check_tool_version", check_tool_version)
    manager.register_validator("check_workspace_integrity", check_workspace_integrity)
    manager.register_validator("check_planning_docs", check_planning_docs)
    manager.register_validator("check_beads_issue", check_beads_issue)
    manager.register_validator("check_plan_approval", check_plan_approval)
    from agent_harness.compliance import check_harness_session, check_hook_integrity

    manager.register_validator("check_harness_session", check_harness_session)
    manager.register_validator("check_hook_integrity", check_hook_integrity)

    # Run initialization phase
    passed, blockers, warnings = manager.run_phase("initialization")

    # Add step to progress
    step = {
        "index": state["current_step_index"],
        "task_id": "Initialization",
        "action": "Run JSON-based Initialization Check",
        "outcome": f"Passed: {passed}. Blockers: {len(blockers)}, Warnings: {len(warnings)}",
        "status": "success" if passed else "failure",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        **state,
        "initialization_passed": passed,
        "blockers": blockers,
        "warnings": warnings,
        "current_phase": "Execution" if passed else "BLOCKED",
        "steps_completed": state.get("steps_completed", []) + [step],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }
