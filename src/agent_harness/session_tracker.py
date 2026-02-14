import json
import time
from pathlib import Path
from typing import Optional, Any
from functools import wraps


class SessionTracker:
    """Track agent sessions and enforce compliance."""

    # Use a hidden directory in the home folder for cross-project session tracking if needed,
    # but for now, we'll use a project-local .agent/session directory.
    SESSION_DIR = Path.cwd() / ".agent" / "sessions"
    SESSION_FILE = SESSION_DIR / "session.lock"
    SESSION_LOG = SESSION_DIR / "sessions.jsonl"

    def __init__(self):
        self.SESSION_DIR.mkdir(parents=True, exist_ok=True)

    def init_session(self, mode: str, issue_id: str) -> str:
        """Initialize a new session."""
        if self.has_active_session():
            session = self.get_session()
            if session and session.get("issue_id") == issue_id:
                return session["id"]
            raise Exception(
                f"Active session for issue {session.get('issue_id')} already exists. "
                "Close it first before starting a new one."
            )

        session_id = f"sess_{int(time.time())}"
        session_data = {
            "id": session_id,
            "mode": mode,
            "issue_id": issue_id,
            "started_at": time.time(),
            "status": "active",
        }

        self.SESSION_FILE.write_text(json.dumps(session_data))

        # Log session start
        with open(self.SESSION_LOG, "a") as f:
            f.write(json.dumps({**session_data, "event": "session_started"}) + "\n")

        return session_id

    def has_active_session(self) -> bool:
        """Check if active session exists and is not expired (8h)."""
        if not self.SESSION_FILE.exists():
            return False

        try:
            session = json.loads(self.SESSION_FILE.read_text())
            # Check expiration (8 hours)
            if time.time() - session["started_at"] > 8 * 3600:
                self.close_session(status="expired")
                return False
            return session.get("status") == "active"
        except Exception:
            return False

    def get_session(self) -> Optional[dict]:
        """Get current session data."""
        if not self.has_active_session():
            return None
        try:
            return json.loads(self.SESSION_FILE.read_text())
        except Exception:
            return None

    def close_session(self, status: str = "completed"):
        """Close the current session."""
        if not self.SESSION_FILE.exists():
            return

        try:
            session = json.loads(self.SESSION_FILE.read_text())
            session["status"] = status
            session["ended_at"] = time.time()

            # Log session end
            with open(self.SESSION_LOG, "a") as f:
                f.write(json.dumps({**session, "event": "session_ended"}) + "\n")
        except Exception:
            pass

        self.SESSION_FILE.unlink(missing_ok=True)

    @classmethod
    def require_session(cls, func: Any):
        """Decorator to require active session."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            tracker = cls()
            if not tracker.has_active_session():
                raise Exception(
                    "No active harness session. "
                    "Initialize with: python check_protocol_compliance.py --init"
                )
            return func(*args, **kwargs)

        return wrapper
