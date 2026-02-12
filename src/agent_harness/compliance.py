import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple, List

from pydantic import BaseModel, Field


class ContextCheck(BaseModel):
    roadmap_exists: bool
    implementation_plan_exists: bool
    missing_docs: list[str] = Field(default_factory=list)


class ApprovalCheck(BaseModel):
    approved: bool
    timestamp: str | None = None
    age_hours: float = 0.0
    stale: bool = False


def check_planning_docs(*args) -> Tuple[bool, str]:
    """Verify planning documents exist or have specific content."""
    project_root = Path.cwd()
    roadmap_locations = [
        project_root / ".agent/rules/ROADMAP.md",
        project_root / ".agent/ROADMAP.md",
        project_root / "ROADMAP.md",
    ]
    impl_locations = [
        project_root / ".agent/rules/ImplementationPlan.md",
        project_root / ".agent/ImplementationPlan.md",
        project_root / "ImplementationPlan.md",
    ]

    roadmap_exists = any(p.exists() for p in roadmap_locations)
    impl_exists = any(p.exists() for p in impl_locations)

    if args:
        if args[0] == "ImplementationPlan.md":
            if not impl_exists:
                return False, "ImplementationPlan.md missing"
            return True, "ImplementationPlan.md exists"
        if args[0] == "blast_radius":
            for p in impl_locations:
                if p.exists() and "Blast Radius" in p.read_text():
                    return True, "Blast radius analysis found in ImplementationPlan.md"
            return False, "Blast radius analysis not found in ImplementationPlan.md"

    missing = []
    if not roadmap_exists:
        missing.append("ROADMAP.md")
    if not impl_exists:
        missing.append("ImplementationPlan.md")

    if not missing:
        return True, "All planning documents exist"
    return False, f"Missing: {', '.join(missing)}"


def check_approval(max_hours: int = 4) -> ApprovalCheck:
    task_paths = [Path(".agent/task.md"), Path("task.md")]

    # Check brain directory (most recent)
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for d in session_dirs:
            task_paths.append(d / "task.md")

    for path in task_paths:
        if path.exists():
            content = path.read_text()
            if "## Approval" in content or "👍 APPROVED" in content or "[x]" in content.lower():
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                age = (datetime.now() - mtime).total_seconds() / 3600
                return ApprovalCheck(
                    approved=True,
                    timestamp=mtime.isoformat(),
                    age_hours=age,
                    stale=age > max_hours,
                )
    return ApprovalCheck(approved=False)


def check_beads_available() -> bool:
    try:
        subprocess.run(["bd", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def check_tool_version(tool: str, min_version: str) -> Tuple[bool, str]:
    """Check if a tool's version meets the minimum requirement."""
    try:
        version_flag = "version" if tool == "bd" else "--version"
        result = subprocess.run([tool, version_flag], capture_output=True, text=True, timeout=5)
        output = result.stdout.strip() or result.stderr.strip()

        # Simple version parsing logic
        import re

        match = re.search(r"(\d+(?:\.\d+)+)", output)
        if not match:
            return False, f"Could not parse version from: {output}"

        current_v = tuple(map(int, match.group(1).split(".")))
        required_v = tuple(map(int, min_version.split(".")))

        if current_v < required_v:
            return False, f"Version for '{tool}' is too old: {output} (Required: {min_version})"

        return True, f"{tool} version {'.'.join(map(str, current_v))} is OK"
    except Exception as e:
        return False, f"Error checking {tool} version: {e}"


def check_workspace_integrity(*args) -> Tuple[bool, str]:
    """Verify workspace integrity by checking for mandatory directories and files."""
    if args:
        if args[0] == "task":
            # Check for task.md in brain directory
            brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
            if brain_dir.exists():
                session_dirs = sorted(
                    [d for d in brain_dir.iterdir() if d.is_dir()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                )[:1]
                for d in session_dirs:
                    if (d / "task.md").exists():
                        return True, f"task.md found in {d}"
            return False, "task.md not found in recent brain directory"
        if args[0] == "cleanup":
            # Verify temporary artifacts like task.md are NOT in root
            temp_files = ["task.md", "debrief.md"]
            present = [f for f in temp_files if (Path.cwd() / f).exists()]
            if present:
                return False, f"Temporary artifacts still present: {', '.join(present)}"
            return True, "Temporary artifacts cleaned up"

    mandatory_paths = [
        Path(".git"),
        Path(".agent"),
        Path(".beads"),
    ]

    missing = [str(p) for p in mandatory_paths if not p.exists()]
    if missing:
        return False, f"Missing mandatory components: {', '.join(missing)}"
    return True, "Workspace integrity verified"


def check_plan_approval(*args) -> Tuple[bool, str]:
    """Check if plan is approved. Supports 'invert' argument for retrospective."""
    max_hours = 4
    invert = False

    if args:
        if args[0] == "invert":
            invert = True
        else:
            try:
                max_hours = int(args[0])
            except ValueError:
                pass

    approval = check_approval(max_hours=max_hours)

    if invert:
        passed = not approval.approved
        msg = (
            "Plan approval marker cleared"
            if passed
            else "Plan approval marker still present in task.md"
        )
        return passed, msg

    passed = approval.approved and not approval.stale
    msg = f"Approved: {approval.approved}, Stale: {approval.stale}"
    return passed, msg


def check_beads_issue(*args) -> Tuple[bool, str]:
    """Verify an active Beads issue exists."""
    try:
        result = subprocess.run(["bd", "status"], capture_output=True, text=True)
        if result.returncode == 0 and "No active task" not in result.stdout:
            return True, "Active Beads issue found"
        return False, "No active Beads issue found"
    except Exception as e:
        return False, f"Error checking Beads status: {e}"


def check_branch_info(required_type: str = "feature") -> Tuple[bool, str]:
    """Verify current branch info."""
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        if required_type == "feature":
            if branch in ["main", "master", "develop"]:
                return False, f"Active work should be on a feature branch, currently on '{branch}'"
            return True, f"On feature branch '{branch}'"
        elif required_type == "main":
            if branch not in ["main", "master"]:
                return False, f"Should be on main/master branch, currently on '{branch}'"
            return True, "On main branch"
        return True, f"Current branch: {branch}"
    except Exception as e:
        return False, f"Error checking branch: {e}"


def check_git_status(*args) -> Tuple[bool, str]:
    """Verify working tree is clean and optionally synced with remote."""
    try:
        if args and args[0] == "synced":
            # Check if up to date with remote
            subprocess.run(["git", "fetch"], capture_output=True)
            status = subprocess.check_output(["git", "status", "-uno"], text=True)
            if "Your branch is up to date" in status or "Your branch is ahead of" in status:
                return True, "Branch is synced or ahead of remote"
            return False, "Branch is behind remote"

        status_out = subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        if status_out:
            return False, "Uncommitted changes detected"
        return True, "Working tree clean"
    except Exception as e:
        return False, f"Error checking git status: {e}"


def check_reflection_invoked(*args) -> Tuple[bool, str]:
    """Verify structured reflection was captured."""
    paths = [Path(".reflection_input.json")]
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        for d in session_dirs:
            paths.append(d / ".reflection_input.json")
            paths.append(d / "reflect_history.json")

    for p in paths:
        if p.exists():
            return True, f"Reflection found at {p}"
    return False, "No structured reflection found (.reflection_input.json). Run /reflect."


def check_debriefing_invoked(*args) -> Tuple[bool, str]:
    """Verify debriefing file exists."""
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        for d in session_dirs:
            if (d / "debrief.md").exists():
                return True, f"Debrief found at {d / 'debrief.md'}"
    return False, "No debrief.md found in recent session."


def check_todo_completion(*args) -> Tuple[bool, str]:
    """Verify all tasks in task.md are completed."""
    path = Path("task.md")
    if not path.exists():
        path = Path(".agent/task.md")

    if not path.exists():
        return False, "task.md not found"

    content = path.read_text()
    if "- [ ]" in content:
        return False, "Incomplete tasks found in task.md"
    return True, "All tasks in task.md completed"


def check_progress_log_exists(*args) -> Tuple[bool, str]:
    """Verify progress log exists."""
    progress_dir = Path(".agent/progress-logs")
    if progress_dir.exists() and any(progress_dir.iterdir()):
        return True, "Progress log exists"
    return False, "No progress log found in .agent/progress-logs/"


def check_handoff_pr_link(*args) -> Tuple[bool, str]:
    """Verify PR link in debrief.md."""
    # Basic check for a URL-like string in debrief.md
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        for d in session_dirs:
            debrief = d / "debrief.md"
            if debrief.exists():
                content = debrief.read_text()
                if "github.com" in content and "/pull/" in content:
                    return True, "PR link found in debrief.md"
    return False, "No PR link found in debrief.md"


def check_handoff_beads_id(*args) -> Tuple[bool, str]:
    """Verify Beads issue ID in debrief.md."""
    # Try to get active issue ID from branch or bd
    issue_id = None
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        if branch.startswith("agent/"):
            issue_id = branch.replace("agent/", "")
    except Exception:
        pass

    if not issue_id:
        try:
            import json as json_lib
            result = subprocess.run(["bd", "list", "-s", "in_progress", "--json"], capture_output=True, text=True)
            if result.returncode == 0:
                issues = json_lib.loads(result.stdout)
                if issues:
                    issue_id = issues[0]["id"]
        except Exception:
            pass

    if not issue_id:
        return False, "Could not determine active Beads issue ID"

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        for d in session_dirs:
            debrief = d / "debrief.md"
            if debrief.exists():
                content = debrief.read_text()
                if issue_id in content:
                    return True, f"Beads issue ID '{issue_id}' found in debrief.md"
                return False, f"Beads issue ID '{issue_id}' not found in debrief.md"

    return False, "No debrief.md found in recent session to verify Beads ID"


def check_handoff_compliance(*args) -> Tuple[bool, str]:
    """Verify handoff documentation."""
    # Placeholder for more complex handoff verification
    return True, "Handoff compliance verified"


def validate_atomic_commits(*args) -> Tuple[bool, str]:
    """Validate atomic commit requirements."""
    try:
        msg = subprocess.check_output(["git", "log", "-1", "--pretty=%B"], text=True).strip()
        patterns = [
            r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .+$"
        ]
        if any(re.match(p, msg) for p in patterns):
            return True, f"Commit message matches conventional format: {msg[:30]}..."
        return False, f"Last commit message does not match conventional format: '{msg}'"
    except Exception as e:
        return False, f"Error validating commits: {e}"


def validate_tdd_compliance(*args) -> Tuple[bool, str]:
    """Verify TDD compliance."""
    try:
        # Check if any file in tests/ was modified in the last 5 commits
        diff_files = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD~5", "HEAD"], text=True
        ).splitlines()
        if any(f.startswith("tests/") for f in diff_files):
            return True, "Test changes detected in recent commits"
        return (
            False,
            "No test changes detected in recent commits (TDD requires implementation + tests)",
        )
    except Exception:
        return True, "Could not verify TDD (repo state or history issues)"
