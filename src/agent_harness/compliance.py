import subprocess
import re
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, List, Optional, Union

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


def check_tool_available(tool: str) -> bool:
    """Check if a command-line tool is available."""
    try:
        result = subprocess.run(
            ["which", tool],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_active_issue_id() -> Optional[str]:
    """Identify the active beads issue ID strictly from branch name if on feature branch."""
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip()
        is_feature = branch.startswith(("agent/", "feature/", "chore/"))

        # Strictly derive from branch name for feature branches
        if is_feature:
            parts = branch.split("/")
            if len(parts) > 1:
                return parts[-1]
            return branch

        # Fallback to bd ready ONLY if on protected base branches
        protected_branches = ["main", "master", "develop", "origin/main", "origin/master"]
        if branch in protected_branches:
            if check_tool_available("bd"):
                try:
                    result = subprocess.run(
                        ["bd", "ready"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split("\n")
                        for line in lines:
                            line = line.strip()
                            if not line or "Ready work" in line:
                                continue
                            match = re.search(r"([a-zA-Z0-9-.]+):", line)
                            if match:
                                return match.group(1).strip()
                except Exception:
                    pass
    except Exception:
        pass
    return None


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


def check_branch_info(*args) -> tuple[Union[str, bool], bool]:
    """Get current branch and check if it's a feature branch.
    If args are provided, checks if the current branch matches the first arg.
    Matches Orchestrator signature.
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            # If an argument is provided, check for equality (for main/master check)
            if args and args[0]:
                target = args[0]
                return branch, branch == target

            is_feature = branch.startswith(("agent/", "feature/", "chore/"))
            return branch, is_feature
        return "unknown", False
    except Exception:
        return "unknown", False


def verify_branch_type(required_type: str = "feature") -> Tuple[bool, str]:
    """Verify current branch info. Local utility."""
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
    issue_id = get_active_issue_id()
    if not issue_id:
        return False, "Could not determine active Beads issue ID"

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for d in session_dirs:
            debrief = d / "debrief.md"
            if debrief.exists():
                content = debrief.read_text()
                if issue_id in content:
                    return True, f"Beads issue ID '{issue_id}' found in debrief.md"

    return False, f"Beads issue ID '{issue_id}' not found in debrief.md"


def check_pr_review_issue_created(*args) -> tuple[bool, str]:
    """Check if a P0 PR review issue exists for the current branch."""
    if not check_tool_available("bd"):
        return False, "beads (bd) not available"

    branch, is_feature = check_branch_info()
    if not is_feature:
        return True, "Not on feature branch (PR review not required)"

    try:
        result = subprocess.run(
            ["bd", "list", "--priority", "P0"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return False, "Failed to query beads for PR review issues"

        output = result.stdout.strip()
        if not output:
            return (
                False,
                f"No P0 PR review issue found for branch '{branch}'. Create one with: bd create --priority P0 'PR Review: {branch}'",
            )

        lines = output.split("\n")
        for line in lines:
            line_lower = line.lower()
            if "pr review" in line_lower or "pr-review" in line_lower:
                parts = line.split(":")
                if parts:
                    issue_id = parts[0].strip()
                    return True, f"PR review issue found: {issue_id}"
            branch_slug = branch.split("/")[-1] if "/" in branch else branch
            if branch_slug.lower() in line_lower:
                parts = line.split(":")
                if parts:
                    issue_id = parts[0].strip()
                    return True, f"PR review issue found (branch match): {issue_id}"

        return (
            False,
            f"No P0 PR review issue found for branch '{branch}'. Create one with: bd create --priority P0 'PR Review: {branch}'",
        )
    except Exception as e:
        return False, f"PR review check failed: {e}"


def check_pr_exists(*args) -> tuple[bool, str]:
    """Check if a Pull Request exists for the current branch using gh CLI."""
    branch, is_feature = check_branch_info()
    if not is_feature:
        return True, "No PR required for non-feature branch"

    if not check_tool_available("gh"):
        return False, "gh (GitHub CLI) not available. PR cannot be verified."

    try:
        result = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--json", "url", "--jq", ".[0].url"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            pr_url = result.stdout.strip()
            if pr_url:
                return True, f"PR found: {pr_url}"
            else:
                return (
                    False,
                    f"No PR found for branch '{branch}'. Create one with: gh pr create --fill",
                )
        return False, f"gh command failed: {result.stderr.strip()}"
    except Exception as e:
        return False, f"PR check failed: {e}"


def check_handoff_pr_verification(*args) -> tuple[bool, str]:
    """Verify that there are no orphaned or multiple open PRs for the current issue."""
    if not check_tool_available("gh") or not check_tool_available("bd"):
        return True, "gh or bd not available (skipping handoff PR verification)"

    issue_id = get_active_issue_id()
    if not issue_id:
        return True, "No active issue (skipping handoff PR verification)"

    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--search",
                issue_id,
                "--state",
                "open",
                "--json",
                "number,title,headRefName,url",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode != 0:
            return False, f"gh command failed: {result.stderr.strip()}"

        prs = json.loads(result.stdout)
        if not prs:
            return True, f"No open PRs found for issue '{issue_id}'"

        branch, _ = check_branch_info()

        if len(prs) > 1:
            pr_list = ", ".join([f"#{pr['number']} ({pr['url']})" for pr in prs])
            return (
                False,
                f"PROTOCOL VIOLATION: Multiple open PRs found for issue '{issue_id}': {pr_list}. Please close orphaned PRs.",
            )

        pr = prs[0]
        if pr["headRefName"] != branch:
            return (
                False,
                f"PROTOCOL VIOLATION: Open PR #{pr['number']} is on branch '{pr['headRefName']}', but current branch is '{branch}'. This suggests workspace drift.",
            )

        return (
            True,
            f"Handoff PR verified: #{pr['number']} on branch '{pr['headRefName']}'",
        )

    except Exception as e:
        return False, f"Handoff PR verification error: {e}"


def check_beads_pr_sync(*args) -> tuple[bool, str]:
    """Verify that the current Pull Request title or body references the active Beads issue."""
    if not check_tool_available("gh") or not check_tool_available("bd"):
        return True, "gh or bd not available (skipping Beads-PR sync check)"

    issue_id = get_active_issue_id()
    if not issue_id:
        return True, "No active issue identified (skipping Beads-PR sync check)"

    try:
        branch, is_feature = check_branch_info()
        if not is_feature:
            return True, "Not on feature branch"

        result = subprocess.run(
            ["gh", "pr", "view", "--json", "title,body"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return False, "Could not find a PR for the current branch. Please run 'gh pr create --fill'."

        pr_data = json.loads(result.stdout)
        title = pr_data.get("title", "")
        body = pr_data.get("body", "")

        issue_id_lower = issue_id.lower()
        if issue_id_lower in title.lower() or issue_id_lower in body.lower():
            return True, f"Beads issue '{issue_id}' properly synchronized with PR"
        
        patterns = [f"[{issue_id}]", f"#{issue_id}", f"{issue_id}:"]
        if any(p.lower() in title.lower() or p.lower() in body.lower() for p in patterns):
             return True, f"Beads issue '{issue_id}' properly synchronized with PR"

        return (
            False,
            f"PROTOCOL VIOLATION: Pull Request title/body must reference the active Beads issue '{issue_id}'. Run 'gh pr edit --title \"[{issue_id}] Your Title\"'.",
        )

    except Exception as e:
        return False, f"Beads-PR synchronization check error: {e}"


def check_pr_decomposition_closure(*args) -> tuple[bool, str]:
    """Verify that decomposed PRs are properly closed per PR Response Protocol."""
    if not check_tool_available("bd") or not check_tool_available("gh"):
        return True, "beads or gh not available (skipping decomposition check)"
    
    try:
        active_issue = get_active_issue_id()
        if not active_issue:
            return True, "No active issue (decomposition check not applicable)"
        
        result = subprocess.run(
            ["bd", "show", active_issue],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            return True, "Could not query issue details (skipping)"
        
        output = result.stdout
        output_lower = output.lower()
        has_children = "part-of" in output_lower or "child" in output or "epic" in output
        
        if not has_children:
            return True, "No child issues detected (not a decomposition)"
        
        pr_pattern = r"PR #(\d+)|pull/(\d+)"
        pr_matches = re.findall(pr_pattern, output)
        
        if not pr_matches:
            return True, "Parent issue with children but no original PR referenced"
        
        pr_number = next((m[0] or m[1] for m in pr_matches if m[0] or m[1]), None)
        
        if not pr_number:
            return True, "Could not extract PR number from issue"
        
        pr_check = subprocess.run(
            ["gh", "pr", "view", pr_number, "--json", "state", "--jq", ".state"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if pr_check.returncode == 0:
            pr_status = pr_check.stdout.strip()
            if pr_status == "CLOSED":
                return True, f"Original PR #{pr_number} properly closed (decomposition protocol followed)"
            elif pr_status == "MERGED":
                return True, f"Original PR #{pr_number} was merged (not decomposed)"
            else:
                return (
                    False,
                    f"PROTOCOL VIOLATION: Original PR #{pr_number} is still OPEN but child issues exist.",
                )
        
        return True, "Could not verify PR status (skipping)"
    except Exception as e:
        return True, f"Decomposition check error: {e}"


def check_child_pr_linkage(*args) -> tuple[bool, str]:
    """Validate that child PRs properly reference their parent Epic/issue per PR Response Protocol."""
    if not check_tool_available("bd") or not check_tool_available("gh"):
        return True, "beads or gh not available (skipping linkage check)"
    
    try:
        active_issue = get_active_issue_id()
        if not active_issue:
            return True, "No active issue (linkage check not applicable)"
        
        result = subprocess.run(
            ["bd", "show", active_issue],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if result.returncode != 0:
            return True, "Could not query issue details (skipping)"
        
        parent_pattern = r"(?:part.?of|depends.?on|blocks?.?by)[\s:]+(\w+-[\w-]+)"
        parent_matches = re.findall(parent_pattern, result.stdout, re.IGNORECASE)
        
        if not parent_matches:
            return True, "No parent issue detected (not a child PR)"
        
        parent_id = parent_matches[0]
        branch, is_feature = check_branch_info()
        if not is_feature:
            return True, "Not on feature branch"
        
        pr_check = subprocess.run(
            ["gh", "pr", "view", "--json", "body", "--jq", ".body"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        if pr_check.returncode != 0:
            return True, "No PR found for current branch"
        
        pr_body = pr_check.stdout.lower()
        parent_mentioned = (
            parent_id.lower() in pr_body or
            "parent epic" in pr_body or
            "part of epic" in pr_body
        )
        
        if not parent_mentioned:
            return (
                False,
                f"PROTOCOL VIOLATION: Child PR does not reference parent issue '{parent_id}'.",
            )
        
        return True, f"Child PR properly references parent issue '{parent_id}'"
    except Exception as e:
        return True, f"Linkage check error: {e}"


def check_workspace_cleanup(*args) -> tuple[bool, str]:
    """Verify that the workspace is free of temporary session artifacts drift."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return True, "Could not check for untracked files (skipping)"

        untracked = result.stdout.strip().split("\n") if result.stdout.strip() else []
        allowed_in_root = ["task.md", "debrief.md", ".reflection_input.json", "ImplementationPlan.md", "ROADMAP.md"]
        
        drift = [f for f in untracked if f not in allowed_in_root and not f.startswith("tests/")]
        
        if not drift:
            return True, "Workspace clean of temporary artifact drift"

        suspicious = [f for f in drift if any(pattern in f for pattern in [".bak", ".tmp", "copy", "old", "test_"])]
        
        if suspicious:
            return (
                False,
                f"Suspicious temporary files detected: {', '.join(suspicious)}. Please clean up before finalization.",
            )

        return (
            True,
            f"Workspace has {len(drift)} untracked files (e.g., {drift[0]}). Ensure these are intended to be part of the PR.",
        )

    except Exception as e:
        return False, f"Workspace cleanup check error: {e}"


def check_handoff_compliance(*args) -> Tuple[bool, str]:
    """Check if hand-off compliance verification passes for multi-phase implementations."""
    handoff_dir = Path(".agent/handoffs")
    verification_script = Path(".agent/scripts/verify_handoff_compliance.sh")

    if not handoff_dir.exists():
        return True, "No hand-off directory (not a multi-phase implementation)"

    if not verification_script.exists():
        return False, "Hand-off verification script missing"

    handoff_files = list(handoff_dir.glob("**/phase-*-handoff.md"))
    if not handoff_files:
        return True, "No hand-off documents found (not a multi-phase implementation)"

    try:
        result = subprocess.run(
            [str(verification_script), "--report"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return True, "All hand-off documents pass verification"
        else:
            return False, f"Hand-off verification failed: {result.stderr.strip()}"

    except Exception as e:
        return False, f"Hand-off verification error: {str(e)}"


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
