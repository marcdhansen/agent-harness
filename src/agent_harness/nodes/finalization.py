import subprocess
from datetime import datetime
from pathlib import Path

from agent_harness.state import ProtocolState


def finalization_node(state: ProtocolState) -> ProtocolState:
    """
    Node for performing the Finalization checks.
    """
    blockers = []

    # 1. Git Status Check
    try:
        status_out = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True
        ).strip()
        if status_out:
            blockers.append("Uncommitted changes detected in repository")
    except Exception as e:
        blockers.append(f"Failed to check git status: {str(e)}")

    # 2. Reflection Check (look for recent reflection in brain or logs)
    reflection_found = False
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        # Look for reflect_history.json or similar in recent session dirs
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        for d in session_dirs:
            if (d / "reflect_history.json").exists() or (d / "debrief.md").exists():
                reflection_found = True
                break

    if not reflection_found:
        blockers.append("No recent reflection found. Invoke /reflect before Finalization.")

    finalization_passed = len(blockers) == 0

    # Add step to progress
    step = {
        "index": state["current_step_index"],
        "task_id": "Finalization",
        "action": "Run Finalization check",
        "outcome": f"Passed: {finalization_passed}. Blockers: {len(blockers)}",
        "status": "success" if finalization_passed else "failure",
        "timestamp": datetime.now().isoformat(),
    }

    return {
        **state,
        "finalization_passed": finalization_passed,
        "blockers": blockers,
        "current_phase": "Retrospective" if finalization_passed else "FINALIZATION_BLOCKED",
        "steps_completed": [step],
        "current_step_index": state["current_step_index"] + 1,
        "last_updated": datetime.now().isoformat(),
    }


def retrospective_node(state: ProtocolState) -> ProtocolState:
    """
    Node for generating the retrospective and syncing to memory.
    """
    print(f"🎖️ Retrospective for {state['process_id']}")

    # Placeholder for actual retrospective generation logic
    # In a real system, this would call specialized agents or tools

    return {
        **state,
        "current_phase": "COMPLETE",
        "last_updated": datetime.now().isoformat(),
    }
