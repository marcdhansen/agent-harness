#!/usr/bin/env python3
"""
Agent Harness - Project-Local Orchestrator & CLI
Provides session management, hook installation, and protocol compliance checks.
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

# Add src to path for absolute imports if needed
sys.path.append(str(Path(__file__).parent / "src"))

from agent_harness.compliance import get_active_issue_id
from agent_harness.session_tracker import CleanupViolationError, SessionTracker


def install_hooks():
    """Install git pre-commit hooks."""
    project_root = Path(__file__).parent
    hook_template = project_root / "src" / "agent_harness" / "scripts" / "hooks" / "pre-commit"
    target_hook = project_root / ".git" / "hooks" / "pre-commit"

    if not hook_template.exists():
        print(f"❌ Error: Hook template not found at {hook_template}")
        sys.exit(1)

    if not (project_root / ".git").exists():
        print("❌ Error: Not a git repository or .git directory missing.")
        sys.exit(1)

    print("🔧 Installing git pre-commit hook...")
    shutil.copy(hook_template, target_hook)
    target_hook.chmod(0o755)
    print("✅ Git pre-commit hook installed successfully.")


def init_session(mode: str, issue_id: str):
    """Initialize a new harness session with cleanup validation."""
    tracker = SessionTracker()
    try:
        # Soft cleanup validation at session start
        validation = tracker.validate_session_start()
        if validation.violations:
            tracker.handle_session_start_violations(validation)

        session_id = tracker.init_session(mode=mode, issue_id=issue_id)
        print(f"✅ Session initialized: {session_id}")
        print(f"Mode: {mode}")
        print(f"Issue: {issue_id}")
    except Exception as e:
        print(f"❌ Error initializing session: {e}")
        sys.exit(1)


def close_session(skip_validation: bool = False):
    """Close the current harness session with cleanup validation."""
    tracker = SessionTracker()
    session = tracker.get_session()
    if not session:
        print("ℹ️ No active session to close.")
        return

    try:
        tracker.close_session(validate_cleanup=not skip_validation)
        print(f"✅ Session {session['id']} closed.")
    except CleanupViolationError as e:
        print(f"\n❌ Cannot close session:\n{e}")
        print("\nOptions:")
        print("  1. Clean up violations: rm <file>")
        print(
            "  2. Force close (skip validation): python check_protocol_compliance.py --close --skip-validation"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error closing session: {e}")
        sys.exit(1)


def status():
    """Show current session status with cleanup validation."""
    tracker = SessionTracker()
    session = tracker.get_session()
    if session:
        duration = int((time.time() - session["started_at"]) / 60)
        print(f"✅ Active Session: {session['id']}")
        print(f"   Mode: {session['mode']}")
        print(f"   Issue: {session['issue_id']}")
        print(f"   Duration: {duration} minutes")

        # Show cleanup status
        validation = tracker.validate_finalization()
        if validation.violations:
            print(f"\n⚠️  Cleanup validation: {len(validation.violations)} violations found")
            for v in validation.violations[:5]:
                print(f"   - {v}")
            if len(validation.violations) > 5:
                print(f"   ... and {len(validation.violations) - 5} more")
        else:
            print("\n✅ Cleanup validation: OK")
    else:
        print("❌ No active harness session.")


def main():
    parser = argparse.ArgumentParser(description="Agent Harness CLI")
    parser.add_argument("--init", action="store_true", help="Initialize a new session")
    parser.add_argument("--close", action="store_true", help="Close the current session")
    parser.add_argument("--status", action="store_true", help="Show session status")
    parser.add_argument("--fallback", action="store_true", help="Run manual fallback validation")
    parser.add_argument(
        "--install-hooks", action="store_true", help="Install git policy enforcement hooks"
    )
    parser.add_argument("--mode", default="full", help="Session mode (simple/full)")
    parser.add_argument("--issue", help="Beads issue ID (defaults to active branch issue)")
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip cleanup validation when closing session (use with caution)",
    )

    args = parser.parse_args()

    if args.install_hooks:
        install_hooks()
    elif args.fallback:
        import subprocess

        fallback_script = (
            Path(__file__).parent / "src" / "agent_harness" / "scripts" / "fallback_validation.sh"
        )
        if fallback_script.exists():
            subprocess.run([str(fallback_script)])
        else:
            print("⚠️ Fallback script not found in src/agent_harness/scripts/fallback_validation.sh")
            print("Please perform manual checks per SOP.")
    elif args.init:
        issue_id = args.issue or get_active_issue_id()
        if not issue_id:
            print("❌ Error: Could not determine active issue ID. Please provide --issue <ID>")
            sys.exit(1)
        init_session(args.mode, issue_id)
    elif args.close:
        close_session(skip_validation=args.skip_validation)
    elif args.status:
        status()
    else:
        # If no args, run initialization logic (as a check)
        status()


if __name__ == "__main__":
    main()
