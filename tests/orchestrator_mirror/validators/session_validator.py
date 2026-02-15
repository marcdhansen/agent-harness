import json
from pathlib import Path


def check_harness_session(*args) -> tuple[bool, str]:
    """Verify that a harness session is active for the current workspace."""
    session_file = Path.cwd() / ".agent" / "sessions" / "session.lock"

    if not session_file.exists():
        return False, "No active harness session found. Run orchestrator initialization first."

    try:
        with open(session_file) as f:
            data = json.load(f)

        session_id = data.get("id", "unknown")
        issue_id = data.get("issue_id", "unknown")

        return True, f"Active session found: {session_id} (Tracking: {issue_id})"
    except Exception as e:
        return False, f"Error reading session file: {e}"
