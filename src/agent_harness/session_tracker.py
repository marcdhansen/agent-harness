import json
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Any


@dataclass
class ValidationResult:
    """Result of cleanup validation"""

    passed: bool
    violations: list[str]
    enforcement_level: str  # 'none', 'warning', 'blocking'


class CleanupViolationError(Exception):
    """Raised when cleanup validation fails with blocking enforcement"""

    pass


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

    def get_session(self) -> dict | None:
        """Get current session data."""
        if not self.has_active_session():
            return None
        try:
            return json.loads(self.SESSION_FILE.read_text())
        except Exception:
            return None

    def close_session(self, status: str = "completed", validate_cleanup: bool = True):
        """Close the current session with optional cleanup validation."""
        if not self.SESSION_FILE.exists():
            return

        if validate_cleanup:
            validation = self.validate_finalization()
            if not validation.passed:
                raise CleanupViolationError(
                    "Session cleanup incomplete:\n"
                    + "\n".join(f"  - {v}" for v in validation.violations)
                )

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

    # Cleanup validation methods
    PATTERNS_FILE = Path(".harness/cleanup_patterns.txt")

    def validate_session_start(self) -> ValidationResult:
        """
        Validate workspace cleanup at session start (soft enforcement)

        Checks for leftover artifacts from previous sessions.
        Returns warnings but allows session to start.
        """
        violations = self._scan_workspace()

        return ValidationResult(passed=True, violations=violations, enforcement_level="warning")

    def validate_finalization(self) -> ValidationResult:
        """
        Validate workspace cleanup at session end (hard enforcement)

        Blocks session closure if temporary artifacts remain.
        Skips validation if RUNNING_IN_CI or HARNESS_SKIP_CLEANUP is set.
        """
        # Skip validation in CI/test environments
        import os

        if os.environ.get("RUNNING_IN_CI") or os.environ.get("HARNESS_SKIP_CLEANUP"):
            return ValidationResult(passed=True, violations=[], enforcement_level="none")

        violations = self._scan_workspace()

        return ValidationResult(
            passed=len(violations) == 0,
            violations=violations,
            enforcement_level="blocking" if violations else "none",
        )

    def _scan_workspace(self) -> list[str]:
        """Scan workspace for cleanup violations"""
        if not self.PATTERNS_FILE.exists():
            return []

        violations = []
        workspace = Path.cwd()

        patterns = self._load_patterns()

        for pattern in patterns:
            files = list(workspace.glob(f"**/{pattern}"))

            files = [
                f
                for f in files
                if not any(part.startswith(".git") for part in f.parts)
                and not any(part == "venv" for part in f.parts)
                and not any(part == ".venv" for part in f.parts)
                and not any(part == "node_modules" for part in f.parts)
                and not any(part == "__pycache__" for part in f.parts)
            ]

            for file in files:
                try:
                    rel_path = file.relative_to(workspace)
                    violations.append(str(rel_path))
                except ValueError:
                    pass

        return sorted(set(violations))

    def _load_patterns(self) -> list[str]:
        """Load cleanup patterns from file"""
        if not self.PATTERNS_FILE.exists():
            return []

        patterns = []
        for line in self.PATTERNS_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)

        return patterns

    def handle_session_start_violations(self, validation: ValidationResult):
        """Handle violations at session start (interactive)"""
        print("\n⚠️  WARNING: Leftover artifacts from previous session")
        print("\nFound temporary files:")
        for v in validation.violations[:10]:
            print(f"  - {v}")

        if len(validation.violations) > 10:
            print(f"  ... and {len(validation.violations) - 10} more")

        print("\nOptions:")
        print("1. Clean up now (recommended)")
        print("2. Continue anyway (must clean before PR)")
        print("3. Abort")

        try:
            choice = input("\nEnter choice [1-3]: ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "2"

        if choice == "1":
            self._cleanup_violations(validation.violations)
            print("✅ Cleanup complete\n")
        elif choice == "3":
            raise Exception("Session initialization aborted by user")
        else:
            print("⚠️  Continuing with violations (must clean before PR)\n")
            self._log_override("session_start", validation.violations)

    def _cleanup_violations(self, violations: list[str]):
        """Remove violation files"""
        for violation in violations:
            file_path = Path(violation)
            if file_path.exists():
                try:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        import shutil

                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"⚠️  Could not remove {violation}: {e}")

    def _log_override(self, checkpoint: str, violations: list[str]):
        """Log cleanup override for audit"""
        log_file = Path(".harness/cleanup_overrides.log")
        with open(log_file, "a") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": time.time(),
                        "checkpoint": checkpoint,
                        "violations_count": len(violations),
                        "violations": violations[:5],
                    }
                )
                + "\n"
            )

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
