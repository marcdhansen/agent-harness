#!/usr/bin/env python3
"""
Protocol compliance checker - Agent-friendly version (agent-6x9.6)

Supports multiple input methods for both human and agent use:
- Interactive prompts (humans)
- CLI arguments (agents, automation)
- Environment variables (agents, CI/CD)
- Config file (persistent settings)

Usage:
  # Interactive (human)
  python check_protocol_compliance.py init

  # Non-interactive (agent - recommended)
  python check_protocol_compliance.py init --mode simple --issue-id TASK-123

  # Environment variables (agent, CI)
  export HARNESS_MODE=simple HARNESS_ISSUE_ID=TASK-123
  python check_protocol_compliance.py init

  # Config file (agent, persistent)
  # Set values in .harness/config.json
  python check_protocol_compliance.py init
"""

import argparse
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent_harness.compliance import get_active_issue_id
from agent_harness.session_tracker import CleanupViolationError, SessionTracker


def is_interactive() -> bool:
    """
    Check if running in interactive terminal.

    Returns False if:
    - stdin is not a terminal (piped input)
    - Running in CI environment
    - HARNESS_NON_INTERACTIVE env var set
    """
    if os.environ.get("HARNESS_NON_INTERACTIVE", "").lower() in ("1", "true", "yes"):
        return False

    if not sys.stdin.isatty():
        return False

    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_HOME",
        "CIRCLECI",
        "TRAVIS",
        "BUILDKITE",
        "DRONE",
        "HARNESS_SKIP_CLEANUP",
    ]
    if any(os.environ.get(var) for var in ci_indicators):
        return False

    return True


def load_config() -> dict:
    """Load configuration from .harness/config.json"""
    config_file = Path(".harness/config.json")

    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Invalid JSON in {config_file}: {e}")
        except Exception as e:
            print(f"⚠️  Warning: Could not read {config_file}: {e}")

    return {}


def save_to_config(values: dict):
    """Save values to config file for future use"""
    config_file = Path(".harness/config.json")
    config_file.parent.mkdir(exist_ok=True)

    existing = {}
    if config_file.exists():
        try:
            with open(config_file) as f:
                existing = json.load(f)
        except:
            pass

    existing.update(values)

    with open(config_file, "w") as f:
        json.dump(existing, f, indent=2)


def get_value(
    arg_value: Optional[str],
    env_var: str,
    config_key: str,
    prompt: str,
    default: Optional[str] = None,
    required: bool = True,
    choices: Optional[list] = None,
) -> Optional[str]:
    """
    Get value from multiple sources with priority:
    1. CLI argument (highest priority - explicit)
    2. Environment variable (good for CI/automation)
    3. Config file (persistent settings)
    4. Interactive prompt (only if terminal)
    5. Default value (fallback)

    Raises SystemExit if required value not found.
    """
    if arg_value:
        if choices and arg_value not in choices:
            print(f"❌ Error: Invalid value '{arg_value}'")
            print(f"   Must be one of: {', '.join(choices)}")
            sys.exit(1)
        return arg_value

    env_value = os.environ.get(env_var)
    if env_value:
        if choices and env_value not in choices:
            print(f"❌ Error: Invalid {env_var}='{env_value}'")
            print(f"   Must be one of: {', '.join(choices)}")
            sys.exit(1)
        return env_value

    config = load_config()
    config_value = config.get(config_key)
    if config_value:
        if choices and config_value not in choices:
            print(f"⚠️  Warning: Invalid config value '{config_value}' for {config_key}")
            print(f"   Must be one of: {', '.join(choices)}")
        else:
            return config_value

    if is_interactive():
        try:
            prompt_text = prompt
            if choices:
                prompt_text = f"{prompt} ({'/'.join(choices)})"
            if default:
                prompt_text = f"{prompt_text} [{default}]"

            value = input(f"{prompt_text}: ").strip()

            if not value and default:
                return default

            if value and choices and value not in choices:
                print(f"❌ Invalid choice. Must be one of: {', '.join(choices)}")
                sys.exit(1)

            if value:
                return value
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Cancelled by user")
            sys.exit(1)

    if default is not None:
        return default

    if required:
        print(f"❌ Error: {prompt} is required but not provided")
        print()
        print("Provide via:")
        print(f"  CLI arg:  --{config_key.replace('_', '-')} <value>")
        print(f"  Env var:  {env_var}=<value>")
        print(f"  Config:   .harness/config.json (add '{config_key}: <value>')")
        if is_interactive():
            print(f"  Prompt:   Run interactively and enter when prompted")
        print()
        print("Example:")
        if choices:
            print(
                f"  python check_protocol_compliance.py init --{config_key.replace('_', '-')} {choices[0]}"
            )
        else:
            print(
                f"  python check_protocol_compliance.py init --{config_key.replace('_', '-')} <value>"
            )
        sys.exit(1)

    return None


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
    import shutil

    shutil.copy(hook_template, target_hook)
    target_hook.chmod(0o755)
    print("✅ Git pre-commit hook installed successfully.")


def init_session(args):
    """Initialize session - supports both interactive and non-interactive modes"""
    print("🔒 Initializing agent harness session...")
    if not is_interactive():
        print("   (non-interactive mode)")
    print()

    tracker = SessionTracker()

    if tracker.has_active_session():
        existing = tracker.get_session()
        if existing:
            print(f"⚠️  Active session already exists: {existing['id']}")
            print(f"   Mode: {existing['mode']}")
            print(f"   Issue: {existing['issue_id']}")
            print()

        if not is_interactive():
            print("❌ Close existing session first:")
            print("   python check_protocol_compliance.py close")
            return 1

        response = input("Close existing session and create new one? [y/N]: ").strip().lower()
        if response != "y":
            print("Cancelled")
            return 1

        try:
            tracker.close_session(validate_cleanup=False)
            print("✅ Existing session closed")
            print()
        except Exception as e:
            print(f"❌ Could not close existing session: {e}")
            return 1

    mode = get_value(
        arg_value=args.mode,
        env_var="HARNESS_MODE",
        config_key="mode",
        prompt="Mode",
        default=None,
        required=True,
        choices=["simple", "full"],
    )
    assert mode is not None, "mode is required"

    issue_id = get_value(
        arg_value=args.issue_id,
        env_var="HARNESS_ISSUE_ID",
        config_key="issue_id",
        prompt="Beads issue ID",
        default=None,
        required=True,
    )

    if not issue_id or len(issue_id) < 3:
        print(f"❌ Invalid issue ID: '{issue_id}'")
        print("   Issue ID should be in format: TASK-123, bd-abc123, etc.")
        return 1

    try:
        validation = tracker.validate_session_start()
        if validation.violations:
            tracker.handle_session_start_violations(validation)

        session_id = tracker.init_session(mode=mode, issue_id=issue_id)
        print(f"✅ Session initialized: {session_id}")
        print(f"   Mode: {mode}")
        print(f"   Issue: {issue_id}")
        print()

        if not args.no_save_config:
            try:
                save_to_config({"mode": mode, "issue_id": issue_id, "last_session": session_id})
            except Exception as e:
                print(f"⚠️  Warning: Could not save config: {e}")

        if not args.no_update_beads:
            try:
                subprocess.run(
                    [
                        "bd",
                        "update",
                        issue_id,
                        "--status",
                        "in_progress",
                        "--notes",
                        f"Session started: {session_id}",
                    ],
                    timeout=5,
                    capture_output=True,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
                pass

        return 0

    except Exception as e:
        print(f"❌ Session initialization failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def close_session(args):
    """Close session - supports both interactive and non-interactive modes"""
    print("🔒 Closing agent harness session...")
    if not is_interactive():
        print("   (non-interactive mode)")
    print()

    tracker = SessionTracker()

    if not tracker.has_active_session():
        print("ℹ️  No active session to close")
        return 0

    session = tracker.get_session()

    if not session:
        print("❌ Error: Could not get session details")
        return 1

    try:
        tracker.close_session(validate_cleanup=not args.skip_validation)

        duration = int((time.time() - session["started_at"]) / 60)
        print(f"✅ Session closed: {session['id']}")
        print(f"   Duration: {duration} minutes")
        print()

        if not args.no_update_beads:
            try:
                subprocess.run(
                    [
                        "bd",
                        "update",
                        session["issue_id"],
                        "--status",
                        "open",
                        "--notes",
                        "Session ended",
                    ],
                    timeout=5,
                    capture_output=True,
                )
            except:
                pass

        return 0

    except CleanupViolationError as e:
        print(f"❌ Cannot close session due to cleanup violations:")
        print(f"{e}")
        print()
        print("Options:")
        print("  1. Fix violations:")
        print("     bash .harness/scripts/auto-cleanup.sh")
        print()
        print("  2. Force close (skip validation):")
        print("     python check_protocol_compliance.py close --skip-validation")
        print()
        return 1
    except Exception as e:
        print(f"❌ Session close failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def show_status(args):
    """Show session status"""
    tracker = SessionTracker()

    if not tracker.has_active_session():
        print("ℹ️  No active session")

        config = load_config()
        if config:
            print()
            print("📋 Config settings:")
            for key, value in config.items():
                print(f"   {key}: {value}")

        return 0

    session = tracker.get_session()

    if not session:
        print("❌ Error: Could not get session details")
        return 1

    duration = int((time.time() - session["started_at"]) / 60)

    print("📊 Active Session")
    print(f"   ID: {session['id']}")
    print(f"   Mode: {session['mode']}")
    print(f"   Issue: {session['issue_id']}")
    print(f"   Duration: {duration} minutes")
    print(
        f"   Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['started_at']))}"
    )
    print(f"   Workspace: {session.get('workspace', 'unknown')}")
    print()

    try:
        validation = tracker.validate_finalization()

        if validation.violations:
            print(f"⚠️  Cleanup status: {len(validation.violations)} violation(s)")
            for v in validation.violations[:5]:
                print(f"   - {v}")
            if len(validation.violations) > 5:
                print(f"   ... and {len(validation.violations) - 5} more")
            print()
            print("Fix with: bash .harness/scripts/auto-cleanup.sh")
        else:
            print("✅ Cleanup status: No violations")
    except Exception as e:
        print(f"⚠️  Could not check cleanup status: {e}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Protocol compliance checker - Agent-friendly version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  INTERACTIVE (Human):
    python check_protocol_compliance.py init
    python check_protocol_compliance.py close

  NON-INTERACTIVE (Agent - Recommended):
    python check_protocol_compliance.py init --mode simple --issue-id TASK-123
    python check_protocol_compliance.py close

  ENVIRONMENT VARIABLES (Agent, CI):
    export HARNESS_MODE=simple
    export HARNESS_ISSUE_ID=TASK-123
    python check_protocol_compliance.py init

  CONFIG FILE (Agent, Persistent):
    # Create .harness/config.json with mode and issue_id
    python check_protocol_compliance.py init


For more details, see: .harness/USER_GUIDE.md
        """,
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    init_parser = subparsers.add_parser("init", help="Initialize session")
    init_parser.add_argument("--mode", choices=["simple", "full"], help="Session mode")
    init_parser.add_argument("--issue-id", help="Beads issue ID")
    init_parser.add_argument("--no-save-config", action="store_true", help="Do not save to config")
    init_parser.add_argument("--no-update-beads", action="store_true", help="Do not update beads")

    close_parser = subparsers.add_parser("close", help="Close session")
    close_parser.add_argument(
        "--skip-validation", action="store_true", help="Skip cleanup validation"
    )
    close_parser.add_argument("--no-update-beads", action="store_true", help="Do not update beads")

    status_parser = subparsers.add_parser("status", help="Show session status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "init":
        return init_session(args)
    elif args.command == "close":
        return close_session(args)
    elif args.command == "status":
        return show_status(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
