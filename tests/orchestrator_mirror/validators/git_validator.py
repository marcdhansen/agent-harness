import re
import subprocess
from pathlib import Path

from .common import check_tool_available


def check_workspace_integrity(*args) -> tuple[bool, list[str]]:
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
                        return True, [str(d / "task.md")]
            return False, ["task.md not found in recent brain directory"]
        if args[0] == "cleanup":
            # Verify temporary artifacts like task.md are NOT in root
            temp_files = ["task.md", "debrief.md"]
            present = [f for f in temp_files if (Path.cwd() / f).exists()]
            if present:
                return False, present
            return True, ["No temporary artifacts found"]

    mandatory_paths = [
        Path(".git"),
        Path(".agent"),
        Path(".beads"),
    ]

    missing = []
    for path in mandatory_paths:
        if not path.exists():
            missing.append(str(path))

    return len(missing) == 0, missing


def check_git_status(turbo: bool = False) -> tuple[bool, str]:
    """Check if git working directory is clean. Detects code changes for Turbo escalation."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            changes = result.stdout.strip()
            if not changes:
                return True, "Working directory clean"

            # Detect code changes (.py, .sh, .js, .ts, etc.)
            code_extensions = {".py", ".sh", ".js", ".ts", ".go", ".c", ".cpp"}
            metadata_extensions = {
                ".md",
                ".txt",
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".jsonl",
                ".log",
            }
            safe_filenames = {".gitignore", "uv.lock", "package-lock.json", "poetry.lock"}

            code_changes = []
            metadata_changes = []

            for line in result.stdout.split("\n"):
                if len(line) > 3:
                    file_path = line[3:].strip()
                    # Skip safe files
                    if any(file_path.endswith(f) for f in safe_filenames):
                        continue

                    if any(file_path.endswith(ext) for ext in code_extensions):
                        code_changes.append(file_path)
                    elif any(file_path.endswith(ext) for ext in metadata_extensions):
                        metadata_changes.append(file_path)
                    else:
                        # Other changes (assets, binary, unknown) - treat as potential code for safety
                        code_changes.append(file_path)

            if turbo:
                if code_changes:
                    return (
                        False,
                        f"ESCALATION REQUIRED: Logic changes detected: {', '.join(code_changes)}. Please switch to Full SOP.",
                    )
                else:
                    change_type = "documentation" if metadata_changes else "metadata"
                    return True, f"{change_type.capitalize()} changes only (Turbo safe)"

            return False, f"Uncommitted changes:\n{changes}"
        return False, "Git command failed"
    except Exception as e:
        return False, f"Git check failed: {e}"


def check_rebase_status() -> tuple[bool, str]:
    """Detect hanging rebase or merge states."""
    git_dir = Path(".git")
    if (
        (git_dir / "rebase-merge").exists()
        or (git_dir / "rebase-apply").exists()
        or (git_dir / "MERGE_HEAD").exists()
    ):
        return (
            False,
            "Hanging rebase/merge detected. Use 'git rebase --continue/--abort' or 'git merge --abort'.",
        )
    return True, "No hanging rebase/merge detected"


def check_sop_infrastructure_changes() -> tuple[bool, str]:
    """Check if changes involve SOP infrastructure (Orchestrator, skills, SOP docs).

    SOP infrastructure changes require Full Mode escalation per the SOP Modification workflow.

    Returns:
        tuple[bool, str]: (requires_full_mode, status_message)
    """
    try:
        # Get list of changed files from git diff
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            # Try checking staged changes
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                timeout=10,
            )

        if result.returncode != 0:
            return False, "Could not determine changed files (skipping SOP infrastructure check)"

        changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Define SOP infrastructure patterns
        sop_patterns = [
            ".gemini/antigravity/skills/Orchestrator/scripts/",
            ".gemini/antigravity/skills/",  # Any skill script
            "/SKILL.md",  # Any SKILL.md file
            ".agent/docs/SOP_COMPLIANCE_CHECKLIST.md",
            ".agent/docs/sop/",
            ".gemini/antigravity/skills/sop-modification/",
        ]

        sop_files = []
        for file_path in changed_files:
            if not file_path:
                continue
            # Check if file matches any SOP infrastructure pattern
            if any(pattern in file_path for pattern in sop_patterns):
                sop_files.append(file_path)

        if sop_files:
            files_str = "\n  - ".join(sop_files)
            return (
                True,
                f"SOP infrastructure changes detected (Full Mode required):\n  - {files_str}",
            )

        return False, "No SOP infrastructure changes detected"

    except subprocess.TimeoutExpired:
        return False, "Git command timed out (skipping SOP infrastructure check)"
    except Exception as e:
        return False, f"SOP infrastructure check error (skipping): {e}"


def check_branch_info(*args) -> tuple[str | bool, bool]:
    """Get current branch and check if it's a feature branch.
    If args are provided, checks if the current branch matches the first arg.
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

            # Enforce feature branch naming conventions
            is_feature = "/" in branch and not branch.startswith(
                ("main", "master", "develop", "origin/")
            )
            return branch, is_feature
        return "unknown", False
    except Exception:
        return "unknown", False


def get_active_issue_id() -> str | None:
    """Identify the active beads issue ID strictly from branch name if on feature branch."""
    branch, is_feature = check_branch_info()

    # Strictly derive from branch name for feature branches
    # Strictly derive from branch name for feature branches
    if is_feature:
        # Expected format: agent-harness/<issue-id>-<brief-desc>
        # Example: agent-harness/agent-harness-va4-fix-logic
        parts = branch.split("/")
        if len(parts) > 1:
            slug = parts[-1]
            # Match numeric ID first, then project-id (e.g., agent-harness-abc) or dotted ID
            # Priority: 1. Dotted ID (agent-gbv.18), 2. Project-ID-Number (agent-gbv-18), 3. Project-ID-Hash (CORE-9a3), 4. Numeric ONLY (123)
            match = re.search(
                r"^(.+?\.[0-9]+)(?:-|$)|^(.+?-[0-9]+)(?:-|$)|^(.+?-[a-z0-9]{3})(?:-|$)|^([0-9]+)(?:-|$)",
                slug,
            )
            if match:
                return match.group(1) or match.group(2) or match.group(3) or match.group(4)
            # Fallback if slug is just the ID
            return slug
        return branch

    # Fallback to bd ready ONLY if on protected base branches (main/master/develop)
    # This allows 'bd ready' to provide context for initial planning
    protected_branches = ["main", "master", "develop", "origin/main", "origin/master"]
    if branch in protected_branches:
        if check_tool_available("bd"):
            try:
                result = subprocess.run(["bd", "ready"], capture_output=True, text=True, timeout=5)
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
    return None


def validate_atomic_commits() -> tuple[bool, list[str]]:
    """Validate atomic commit requirements per SOP git-workflow."""
    errors = []

    try:
        # Determine base branch for comparison (prefer origin/main, fallback to main)
        base_branch = "origin/main"
        res = subprocess.run(
            ["git", "rev-parse", "--verify", base_branch],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            base_branch = "main"
            res = subprocess.run(
                ["git", "rev-parse", "--verify", base_branch],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                base_branch = "master"
                res = subprocess.run(
                    ["git", "rev-parse", "--verify", base_branch],
                    capture_output=True,
                    text=True,
                )

        if res.returncode != 0:
            errors.append(
                "Could not identify base branch (main/master/origin/main) for comparison."
            )
            return False, errors

        # Check 1: Count commits ahead of base branch
        result = subprocess.run(
            ["git", "log", "--oneline", f"{base_branch}..HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            errors.append(f"Could not compare with {base_branch}.")
            return False, errors

        commits = [line for line in result.stdout.strip().split("\n") if line]
        commit_count = len(commits)

        if commit_count == 0:
            current_branch, _ = check_branch_info()
            if current_branch in ["main", "master", "origin/main"]:
                upstream = "@{u}"
                res = subprocess.run(
                    ["git", "rev-parse", "--verify", upstream], capture_output=True, text=True
                )
                if res.returncode == 0:
                    result = subprocess.run(
                        ["git", "log", "--oneline", f"{upstream}..HEAD"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    commits = [line for line in result.stdout.strip().split("\n") if line]
                    commit_count = len(commits)
                    if commit_count == 0:
                        return True, []

        if commit_count > 1:
            errors.append(
                f"Multiple commits detected ({commit_count}). Squash required before merging to ensure atomic history."
            )
            errors.append(f"  Run: git rebase -i {base_branch}")

        # Check 2: Detect merge commits
        result = subprocess.run(
            ["git", "log", "--merges", f"{base_branch}..HEAD", "--oneline"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            merge_commits = result.stdout.strip().split("\n")
            errors.append(
                f"Merge commits not allowed ({len(merge_commits)} detected). Merge commits are strictly forbidden by SOP."
            )
            errors.append(f"  Action: Rebase onto {base_branch} instead of merging it.")
            errors.append(f"  Run: git rebase {base_branch}")
        elif result.returncode != 0:
            errors.append(f"Merge commit check failed for range {base_branch}..HEAD")

        # Check 3 & 4: Validate commit message format
        if commit_count == 1:
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                commit_msg = result.stdout.strip()
                issue_pattern = r"\[([a-zA-Z0-9-\.]+)\]"
                if not re.search(issue_pattern, commit_msg):
                    errors.append("Commit message must include Beads issue ID in format [issue-id]")
                conv_pattern = r"^(\[[^\]]+\] )?(feat|fix|docs|chore|test|refactor|perf|ci|build|style)(\([^)]+\))?: .+"
                if not re.match(conv_pattern, commit_msg.split("\n")[0]):
                    errors.append("Commit message does not follow conventional commit format")

        return len(errors) == 0, errors

    except Exception as e:
        errors.append(f"Atomic commit validation system error: {e}")
        return False, errors


def prune_local_branches(dry_run: bool = False) -> tuple[bool, str]:
    """Prune local branches that have been merged into the base branch (main/master)."""
    try:
        # Determine base branch
        base_branch = "origin/main"
        res = subprocess.run(
            ["git", "rev-parse", "--verify", base_branch],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            base_branch = "main"
            res = subprocess.run(
                ["git", "rev-parse", "--verify", base_branch],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                base_branch = "master"

        # Fetch to update remote refs
        subprocess.run(["git", "fetch", "--prune"], capture_output=True, timeout=10)

        # Get branches merged into base_branch
        result = subprocess.run(
            ["git", "branch", "--merged", base_branch],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return False, f"Failed to list merged branches against {base_branch}"

        branches = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        to_delete = []
        for b in branches:
            # Clean branch name (remove asterisk for current branch)
            b_clean = b.replace("*", "").strip()
            if b_clean in [
                "main",
                "master",
                "develop",
                base_branch,
                "origin/main",
                "origin/master",
            ]:
                continue
            # Only prune feature-like branches
            if b_clean.startswith(("agent/", "feature/", "chore/", "bugfix/", "hotfix/")):
                to_delete.append(b_clean)

        if not to_delete:
            return True, "No merged branches to prune"

        if dry_run:
            return (
                False,
                f"Stale branches detected: {', '.join(to_delete)}. Run --clean or 'git branch -d' to remove.",
            )

        deleted = []
        failed = []
        for b in to_delete:
            # Use -d for safe deletion (already merged check)
            res = subprocess.run(["git", "branch", "-d", b], capture_output=True, text=True)
            if res.returncode == 0:
                deleted.append(b)
            else:
                failed.append(b)

        msg = ""
        if deleted:
            msg += f"Pruned merged branches: {', '.join(deleted)}. "
        if failed:
            msg += f"Failed to prune (may have unmerged changes): {', '.join(failed)}."
            return False, msg.strip()

        return True, msg.strip()

    except Exception as e:
        return False, f"Pruning error: {e}"


def check_closed_issue_branches() -> tuple[bool, str]:
    """Identify local branches that correspond to closed Beads issues."""
    if not check_tool_available("bd"):
        return True, "Beads CLI not available (skipping closed issue branch check)"

    try:
        # Get all local feature branches
        result = subprocess.run(
            ["git", "branch", "--format=%(refname:short)"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return False, "Failed to list local branches"

        local_branches = result.stdout.strip().split("\n")
        feature_branches = [
            b
            for b in local_branches
            if "/" in b and not b.startswith(("main", "master", "develop", "origin/"))
        ]

        if not feature_branches:
            return True, "No local feature branches found"

        # Get all closed issues from Beads in JSON format
        bd_result = subprocess.run(
            ["bd", "list", "--status", "closed", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if bd_result.returncode != 0:
            return True, "Failed to query closed issues from Beads (skipping)"

        try:
            import json

            closed_data = json.loads(bd_result.stdout)
            closed_ids = {issue["id"] for issue in closed_data}
        except Exception:
            return True, "Failed to parse Beads JSON output (skipping)"

        stale_branches = []
        for branch in feature_branches:
            # Extract ID from branch name
            parts = branch.split("/")
            if len(parts) > 1:
                slug = parts[-1]
                match = re.search(
                    r"^([0-9]+)(?:-|$)|^(.+?-[a-z0-9]{3})(?:-|$)|^(.+?\.[0-9]+)(?:-|$)", slug
                )
                issue_id = match.group(1) or match.group(2) or match.group(3) if match else slug

                if issue_id in closed_ids:
                    stale_branches.append(branch)

        if stale_branches:
            return (
                False,
                f"Stale branches for closed issues detected: {', '.join(stale_branches)}. Please prune them.",
            )

        return True, "No stale branches for closed issues found"

    except Exception as e:
        return True, f"Closed issue branch check error: {e}"


def check_branch_issue_coupling() -> tuple[bool, str]:
    """Verify that the current branch ID matches a 'started' Beads issue and follows naming conventions."""
    branch, is_feature = check_branch_info()

    # Protected base branches allowed for initial setup/planning
    protected_branches = ["main", "master", "develop", "origin/main", "origin/master"]

    if not is_feature:
        if branch in protected_branches:
            return True, f"On protected base branch '{branch}'. Use for discovery/planning only."
        else:
            return (
                False,
                f"PROTOCOL VIOLATION: Branch '{branch}' does not follow naming convention ('<prefix>/<issue-id>-<desc>').",
            )

    # Extract ID from branch (e.g., agent/label-harness-34f -> label-harness-34f)
    branch_id = get_active_issue_id()
    if not branch_id:
        return False, f"Could not identify Beads issue ID from branch '{branch}'"

    if not check_tool_available("bd"):
        return True, "Beads CLI not available, coupling check skipped"

    try:
        # Check if the branch_id issue is actually 'started'
        result = subprocess.run(
            ["bd", "show", branch_id, "--json"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False, f"Branch refers to unknown Beads issue: {branch_id}"

        import json

        data = json.loads(result.stdout)
        issue_data = data[0] if isinstance(data, list) else data

        if not issue_data:
            return False, f"Issue {branch_id} data not found"

        labels = issue_data.get("labels", [])

        if "status:started" in labels or "started:true" in labels:
            return True, f"Branch '{branch}' correctly coupled with started issue '{branch_id}'"

        # If it's NOT started, we have a violation
        return (
            False,
            f"PROTOCOL VIOLATION: Branch issue '{branch_id}' is NOT in 'started' state. "
            f"Current labels: {', '.join(labels)}. "
            f"Run 'bd set-state {branch_id} status=started' first.",
        )

    except Exception as e:
        return False, f"Coupling check error: {e}"
