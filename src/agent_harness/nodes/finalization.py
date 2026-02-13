import subprocess
from datetime import datetime
from pathlib import Path

from agent_harness.state import ProtocolState
from agent_harness.checklists import ChecklistManager
from agent_harness.compliance import (
    check_git_status,
    validate_atomic_commits,
    validate_tdd_compliance,
    check_reflection_invoked,
    check_handoff_compliance,
    check_debriefing_invoked,
    check_plan_approval,
    check_progress_log_exists,
    check_handoff_pr_link,
    check_handoff_beads_id,
    check_todo_completion,
    check_beads_pr_sync,
    check_no_separate_review_issues,
    check_pr_exists,
    check_pr_decomposition_closure,
    check_child_pr_linkage,
    check_workspace_cleanup,
    check_handoff_pr_verification,
    check_wrapup_indicator_symmetry,
    check_wrapup_exclusivity,
    inject_debrief_to_beads,
)


def finalization_node(state: ProtocolState) -> ProtocolState:
    """
    Node for performing the Finalization checks using JSON checklists.
    """
    project_root = Path.cwd()
    checklist_dir = project_root / ".agent/rules/checklists"

    manager = ChecklistManager(checklist_dir)

    # Register validators
    manager.register_validator("check_git_status", check_git_status)
    manager.register_validator("validate_atomic_commits", validate_atomic_commits)
    manager.register_validator("validate_tdd_compliance", validate_tdd_compliance)
    manager.register_validator("check_reflection_invoked", check_reflection_invoked)
    manager.register_validator("check_handoff_compliance", check_handoff_compliance)
    manager.register_validator("check_handoff_beads_id", check_handoff_beads_id)
    manager.register_validator("check_beads_pr_sync", check_beads_pr_sync)
    manager.register_validator("check_no_separate_review_issues", check_no_separate_review_issues)
    manager.register_validator("check_pr_exists", check_pr_exists)
    manager.register_validator("check_todo_completion", check_todo_completion)
    manager.register_validator("check_pr_decomposition_closure", check_pr_decomposition_closure)
    manager.register_validator("check_child_pr_linkage", check_child_pr_linkage)
    manager.register_validator("check_workspace_cleanup", check_workspace_cleanup)
    manager.register_validator("check_handoff_pr_verification", check_handoff_pr_verification)

    # Run finalization phase
    passed, blockers, warnings = manager.run_phase("finalization")

    # Add step to progress
    step = {
        "index": state["current_step_index"],
        "task_id": "Finalization",
        "action": "Run JSON-based Finalization Check",
        "outcome": f"Passed: {passed}. Blockers: {len(blockers)}, Warnings: {len(warnings)}",
        "status": "success" if passed else "failure",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        **state,
        "finalization_passed": passed,
        "blockers": blockers,
        "warnings": warnings,
        "current_phase": "Retrospective" if passed else "FINALIZATION_BLOCKED",
        "steps_completed": state.get("steps_completed", []) + [step],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }


def retrospective_node(state: ProtocolState) -> ProtocolState:
    """
    Node for performing the Retrospective check using JSON checklists.
    """
    project_root = Path.cwd()
    checklist_dir = project_root / ".agent/rules/checklists"

    manager = ChecklistManager(checklist_dir)

    # Register validators
    manager.register_validator("check_reflection_invoked", check_reflection_invoked)
    manager.register_validator("check_debriefing_invoked", check_debriefing_invoked)
    manager.register_validator("check_plan_approval", check_plan_approval)
    manager.register_validator("check_progress_log_exists", check_progress_log_exists)
    manager.register_validator("check_handoff_pr_link", check_handoff_pr_link)
    manager.register_validator("check_handoff_beads_id", check_handoff_beads_id)
    manager.register_validator("check_todo_completion", check_todo_completion)
    manager.register_validator("check_wrapup_indicator_symmetry", check_wrapup_indicator_symmetry)
    manager.register_validator("check_wrapup_exclusivity", check_wrapup_exclusivity)
    manager.register_validator("inject_debrief_to_beads", inject_debrief_to_beads)

    # Run retrospective phase
    passed, blockers, warnings = manager.run_phase("retrospective")

    # Add step to progress
    step = {
        "index": state["current_step_index"],
        "task_id": "Retrospective",
        "action": "Run JSON-based Retrospective Check",
        "outcome": f"Passed: {passed}. Blockers: {len(blockers)}, Warnings: {len(warnings)}",
        "status": "success" if passed else "failure",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        **state,
        "retrospective_passed": passed,
        "blockers": blockers,
        "warnings": warnings,
        "current_phase": "COMPLETE" if passed else "RETROSPECTIVE_BLOCKED",
        "steps_completed": state.get("steps_completed", []) + [step],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }
