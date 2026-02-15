import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from .common import check_tool_available
from .git_validator import check_branch_info, get_active_issue_id


def check_reflection_invoked() -> tuple[bool, str]:
    """Check if reflection was recently invoked and follows structured JSON format."""
    input_artifact = Path(".reflection_input.json")
    if input_artifact.exists():
        try:
            with open(input_artifact) as f:
                data = json.load(f)

            required = ["session_name", "outcome", "technical_learnings", "refactoring_candidates"]
            missing = [field for field in required if field not in data]

            if missing:
                return (
                    False,
                    f"Reflection artifact .reflection_input.json is missing required fields: {', '.join(missing)}",
                )

            mtime = datetime.fromtimestamp(input_artifact.stat().st_mtime)
            age = datetime.now() - mtime
            if age < timedelta(hours=2):
                return (
                    True,
                    f"Reflection captured: Structured reflection captured {age.total_seconds() / 60:.0f} minutes ago",
                )
            else:
                return (
                    False,
                    f"No recent reflection: Reflection artifact .reflection_input.json is too old ({age.total_seconds() / 3600:.1f} hours). Please run /reflect again.",
                )
        except json.JSONDecodeError:
            return False, "Reflection artifact .reflection_input.json is malformed JSON"
        except Exception as e:
            return False, f"Error validating reflection artifact: {e}"

    reflection_paths = [
        Path(".agent/reflections.json"),
        Path("reflections.json"),
    ]

    for path in reflection_paths:
        if path.exists():
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                age = datetime.now() - mtime
                if age < timedelta(hours=2):
                    return (
                        True,
                        f"Reflection (legacy) found {age.total_seconds() / 60:.0f} minutes ago. Please generate .reflection_input.json with /reflect.",
                    )
            except Exception:
                pass

    return False, "No recent reflection found. Please run /reflect to capture session learnings."


def check_debriefing_invoked() -> tuple[bool, str]:
    """Check if debriefing was recently invoked."""
    debrief_paths = [Path("debrief.md")]

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]

        for session_dir in session_dirs:
            debrief_paths.append(session_dir / "debrief.md")

    for p in debrief_paths:
        if p.exists():
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                age = datetime.now() - mtime
                if age < timedelta(hours=2):
                    return (
                        True,
                        f"Debrief found {age.total_seconds() / 60:.0f} minutes ago: {p}",
                    )
            except Exception:
                pass

    return False, "No recent debrief found in root or brain directory"


def check_wrapup_indicator_symmetry() -> tuple[bool, str]:
    """Verify 🏁 symmetry:
    1. If 🏁 is in debrief.md, ensure SOP is complete (reflection, ID, PR etc).
    2. If SOP is complete, 🏁 should eventually be in the final summary.
    """
    # Try local debrief first
    debrief_paths = [Path("debrief.md")]

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:1]
        if session_dirs:
            debrief_paths.append(session_dirs[0] / "debrief.md")

    recent_debrief = None
    for p in debrief_paths:
        if p.exists():
            recent_debrief = p
            break

    if not recent_debrief:
        return True, "No recent debrief.md found to check for 🏁"

    content = recent_debrief.read_text()
    has_flag = "🏁" in content

    reflection_exists = Path(".reflection_input.json").exists()
    issue_id = get_active_issue_id()
    has_id = issue_id and issue_id in content
    has_pr = "github.com" in content and "/pull/" in content

    sop_complete = reflection_exists and has_id and has_pr

    if has_flag and not sop_complete:
        missing = []
        if not reflection_exists:
            missing.append("reflection")
        if not has_id:
            missing.append("Beads ID")
        if not has_pr:
            missing.append("PR link")
        return (
            False,
            f"PROTOCOL VIOLATION: 🏁 used but SOP incomplete. Missing: {', '.join(missing)}",
        )

    if sop_complete and not has_flag:
        return (
            False,
            "SOP complete but 🏁 missing from debrief.md. Run finalization_debriefing.py to inject it.",
        )

    return True, "🏁 symmetry verified"


def check_wrapup_exclusivity() -> tuple[bool, str]:
    """Verify 🏁 is NOT used in planning or execution docs."""
    forbidden_docs = [
        "ROADMAP.md",
        "ImplementationPlan.md",
        ".agent/ROADMAP.md",
        ".agent/ImplementationPlan.md",
        ".agent/rules/ROADMAP.md",
        ".agent/rules/ImplementationPlan.md",
    ]

    found_in = []
    for doc in forbidden_docs:
        path = Path(doc)
        if path.exists():
            if "🏁" in path.read_text():
                # Allow it if we are currently working on the 🏁 task itself
                issue_id = get_active_issue_id()
                if issue_id == "agent-harness-b9y":
                    continue
                found_in.append(doc)

    if found_in:
        return (
            False,
            f"PROTOCOL VIOLATION: 🏁 found in forbidden documents: {', '.join(found_in)}. This emoji is reserved for session closure.",
        )

    return True, "🏁 exclusivity verified"


def check_code_review_status() -> tuple[bool, str]:
    """Check if code review skill was recently invoked and passed."""
    import sys

    code_review_script = (
        Path.home() / ".gemini/antigravity/skills/code-review/scripts/code_review.py"
    )
    if not code_review_script.exists():
        return False, "Code Review Skill not installed"

    try:
        result = subprocess.run(
            [sys.executable, str(code_review_script)],
            capture_output=True,
            text=True,
            timeout=10,
            env={**os.environ, "AUTOMATED_MODE": "1"},
        )
        if result.returncode == 0:
            return True, "Code Review passed (Automated check)"
        else:
            return False, "Code Review failed or requires manual intervention"
    except Exception as e:
        return False, f"Code Review check error: {e}"


def check_handoff_compliance() -> tuple[bool, str]:
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

    except subprocess.TimeoutExpired:
        return False, "Hand-off verification timed out"
    except Exception as e:
        return False, f"Hand-off verification error: {str(e)}"


def check_todo_completion() -> tuple[bool, str]:
    """Check if all tasks in task.md are completed (oh-my-opencode pattern)."""
    import sys

    enforcer_script = Path.home() / ".agent/scripts/todo-enforcer.py"
    if enforcer_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(enforcer_script)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return True, "All tasks completed (Sisyphus is happy)"
            else:
                msg = (
                    result.stdout.strip().split("\n")[-1]
                    if result.stdout
                    else "Unfinished tasks detected"
                )
                return False, msg
        except Exception as e:
            return False, f"Todo enforcer error: {e}"

    return True, "Todo enforcer script not found (Skipping)"


def check_linked_repositories() -> tuple[bool, list[str]]:
    """Validate that linked repositories follow SOP. Auto-detects changes in global dirs."""
    errors = []
    global_repos = [
        Path.home() / ".gemini",
        Path.home() / ".agent",
    ]

    task_paths = [Path(".agent/task.md"), Path("task.md")]
    for task_path in task_paths:
        if task_path.exists():
            try:
                content = task_path.read_text()
                paths = re.findall(r"-\s+path:\s+([^\n\s]+)", content)
                for p in paths:
                    try:
                        repo_path = Path(p).expanduser()
                        if repo_path.exists() and repo_path.is_dir():
                            if (repo_path / ".git").exists():
                                global_repos.append(repo_path)
                    except Exception:
                        continue
            except Exception:
                pass

    checked_repos = set()
    for repo in global_repos:
        try:
            repo_abs = str(repo.resolve())
            if repo_abs in checked_repos:
                continue
            checked_repos.add(repo_abs)

            if repo_abs == str(Path(".").resolve()):
                continue

            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_abs,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0:
                status = res.stdout.strip()
                if status:
                    branch_res = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=repo_abs,
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    branch = branch_res.stdout.strip() if branch_res.returncode == 0 else "unknown"

                    if branch in ["main", "master"]:
                        errors.append(
                            f"Linked repo {repo.name} has changes on protected branch '{branch}'. Please use a feature branch."
                        )

                    if branch != "unknown":
                        if check_tool_available("gh"):
                            pr_res = subprocess.run(
                                [
                                    "gh",
                                    "pr",
                                    "list",
                                    "--author",
                                    "@me",
                                    "--head",
                                    branch,
                                ],
                                cwd=repo_abs,
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            if pr_res.returncode == 0 and not pr_res.stdout.strip():
                                errors.append(
                                    f"No PR found for linked repo {repo.name} (branch: {branch})"
                                )
        except Exception:
            pass

    return len(errors) == 0, errors


def check_no_separate_review_issues() -> tuple[bool, str]:
    """Verify that NO separate Beads issues have been created for code review."""
    if not check_tool_available("bd"):
        return True, "beads (bd) not available (skipping review issue prohibition check)"

    branch, is_feature = check_branch_info()
    if not is_feature:
        return True, "Not on feature branch"

    active_issue = get_active_issue_id()

    try:
        # List all open issues
        result = subprocess.run(
            ["bd", "list", "--status", "open"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return True, "Failed to query beads (skipping review issue prohibition check)"

        output = result.stdout.strip()
        if not output:
            return True, "No open issues found"

        lines = output.split("\n")
        violations = []
        for line in lines:
            line_lower = line.lower()
            # If the issue title contains "PR Review" or "Code Review"
            if (
                "pr review" in line_lower
                or "pr-review" in line_lower
                or "code review" in line_lower
            ):
                parts = line.split(":")
                if parts:
                    issue_id = parts[0].strip()
                    # It's a violation if it's NOT the active issue (or if the active issue itself is named "PR Review" which is discouraged)
                    if issue_id != active_issue:
                        violations.append(issue_id)

        if violations:
            return (
                False,
                f"PROTOCOL VIOLATION: Separate review issues detected: {', '.join(violations)}. "
                f"SOP prohibits separate issues for code review. Use the original issue '{active_issue}' instead.",
            )

        return True, "No separate PR review issues detected"
    except Exception as e:
        return True, f"Review issue prohibition check error: {e}"


def check_pr_exists() -> tuple[bool, str]:
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
    except subprocess.TimeoutExpired:
        return False, "gh command timed out"
    except Exception as e:
        return False, f"PR check failed: {e}"


def check_handoff_pr_link() -> tuple[bool, str]:
    """Check if the session handoff (debrief.md) contains a GitHub PR link."""
    # Potential debrief locations
    debrief_paths = [Path("debrief.md")]

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for d in session_dirs:
            debrief_paths.append(d / "debrief.md")

    pr_pattern = r"https://github\.com/[^/]+/[^/]+/pull/\d+"

    for debrief_path in debrief_paths:
        if debrief_path.exists():
            try:
                content = debrief_path.read_text()
                if (
                    "PR Link" in content
                    or "pull request" in content.lower()
                    or "github.com" in content
                ):
                    if re.search(pr_pattern, content):
                        return True, f"PR link found in debrief: {debrief_path}"
            except Exception:
                pass

    return False, "No GitHub PR link found in debrief.md"


def check_handoff_beads_id() -> tuple[bool, str]:
    """Check if the session handoff (debrief.md) contains a Beads issue identifier."""
    # Potential debrief locations
    debrief_paths = [Path("debrief.md")]

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for d in session_dirs:
            debrief_paths.append(d / "debrief.md")

    active_issue = get_active_issue_id()
    if not active_issue:
        return True, "No active issue identified (skipping Beads ID check)"

    # Hardened check: look for specific labels or patterns to avoid false positives
    patterns = [
        rf"\b{re.escape(active_issue)}\b",
        rf"Issue:\s*{re.escape(active_issue)}",
        rf"Beads\s*(?:ID|Issue):\s*{re.escape(active_issue)}",
        rf"\[{re.escape(active_issue)}\]",
    ]

    for debrief_path in debrief_paths:
        if debrief_path.exists():
            try:
                content = debrief_path.read_text()
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        return (
                            True,
                            f"Beads issue ID '{active_issue}' verified in debrief: {debrief_path}",
                        )
            except Exception:
                pass

    return (
        False,
        f"Active Beads issue ID '{active_issue}' not found in debrief.md (Required for handoff transparency)",
    )


def check_pr_decomposition_closure() -> tuple[bool, str]:
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
                return (
                    True,
                    f"Original PR #{pr_number} properly closed (decomposition protocol followed)",
                )
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


def check_child_pr_linkage() -> tuple[bool, str]:
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
            parent_id.lower() in pr_body or "parent epic" in pr_body or "part of epic" in pr_body
        )

        if not parent_mentioned:
            return (
                False,
                f"PROTOCOL VIOLATION: Child PR does not reference parent issue '{parent_id}'.",
            )

        return True, f"Child PR properly references parent issue '{parent_id}'"
    except Exception as e:
        return True, f"Linkage check error: {e}"


def check_progress_log_exists() -> tuple[bool, str]:
    """Check if progress log exists for the active issue."""
    issue_id = get_active_issue_id()
    if not issue_id:
        return False, "Active issue ID not identified"

    log_path = Path(".agent/progress-logs") / f"{issue_id}.md"
    if log_path.exists():
        return True, f"Progress log found: {log_path.name}"
    return False, f"Progress log missing: {log_path.name}"


def check_handoff_pr_verification() -> tuple[bool, str]:
    """Verify that there are no orphaned or multiple open PRs for the current issue."""
    if not check_tool_available("gh") or not check_tool_available("bd"):
        return True, "gh or bd not available (skipping handoff PR verification)"

    issue_id = get_active_issue_id()
    if not issue_id:
        return True, "No active issue (skipping handoff PR verification)"

    try:
        # Search for open PRs containing the issue ID in the title or branch
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
        # Allow drift if we are on main/master and checking a finished task?
        # Actually finalization is usually on a feature branch.
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


def check_beads_pr_sync() -> tuple[bool, str]:
    """Verify that the Pull Request is linked to the Beads issue via title/body AND a Beads comment."""
    if not check_tool_available("gh") or not check_tool_available("bd"):
        return True, "gh or bd not available (skipping Beads-PR sync check)"

    issue_id = get_active_issue_id()
    if not issue_id:
        return True, "No active issue identified (skipping Beads-PR sync check)"

    try:
        # Get the current PR for the branch
        branch, is_feature = check_branch_info()
        if not is_feature:
            return True, "Not on feature branch"

        result = subprocess.run(
            ["gh", "pr", "view", "--json", "title,body,url"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return (
                False,
                "Could not find a PR for the current branch. Please run 'gh pr create --fill'.",
            )

        pr_data = json.loads(result.stdout)
        title = pr_data.get("title", "")
        body = pr_data.get("body", "")
        pr_url = pr_data.get("url", "")

        # 1. Check for issue_id in title or body
        issue_id_lower = issue_id.lower()
        linked_in_pr = issue_id_lower in title.lower() or issue_id_lower in body.lower()

        if not linked_in_pr:
            # Also check for common patterns
            patterns = [f"[{issue_id}]", f"#{issue_id}", f"{issue_id}:"]
            linked_in_pr = any(
                p.lower() in title.lower() or p.lower() in body.lower() for p in patterns
            )

        if not linked_in_pr:
            return (
                False,
                f"PROTOCOL VIOLATION: Pull Request title/body must reference the active Beads issue '{issue_id}'. "
                f"Run 'gh pr edit --title \"[{issue_id}] Your Title\"'.",
            )

        # 2. Check for PR URL in Beads comments
        beads_res = subprocess.run(
            ["bd", "show", issue_id],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if beads_res.returncode != 0:
            return False, f"Failed to query Beads issue '{issue_id}'"

        beads_output = beads_res.stdout
        if pr_url.lower() not in beads_output.lower():
            return (
                False,
                f"PROTOCOL VIOLATION: Beads issue '{issue_id}' must contain a comment with the PR URL. "
                f'Run: bd comments add {issue_id} "PR: {pr_url}"',
            )

        return True, f"Beads issue '{issue_id}' properly synchronized with PR"

    except Exception as e:
        return False, f"Beads-PR synchronization check error: {e}"


def check_issue_closure_gate() -> tuple[bool, str]:
    """Verify that Beads issues remain open (in_review/started) until PRs are merged."""
    if not check_tool_available("gh") or not check_tool_available("bd"):
        return True, "gh or bd not available (skipping closure gate)"

    issue_id = get_active_issue_id()
    if not issue_id:
        return True, "No active issue identified"

    try:
        # 1. Get Beads issue status
        beads_res = subprocess.run(
            ["bd", "show", issue_id, "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if beads_res.returncode != 0:
            return False, f"Failed to query Beads issue '{issue_id}'"

        issue_data_list = json.loads(beads_res.stdout)
        if not issue_data_list:
            return False, f"Issue '{issue_id}' not found in Beads"

        issue_status = issue_data_list[0].get("status", "").lower()
        issue_labels = issue_data_list[0].get("labels", [])
        is_in_review = issue_status == "in_review" or "in_review" in [
            lbl.lower() for lbl in issue_labels
        ]

        # 2. Get associated PRs (searching by issue_id)
        gh_res = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--search",
                issue_id,
                "--state",
                "all",
                "--json",
                "state,number",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if gh_res.returncode != 0:
            return True, "Could not verify PR state via gh (skipping)"

        prs = json.loads(gh_res.stdout)

        # 3. Apply rules
        open_prs = [pr for pr in prs if pr["state"] == "OPEN"]

        if open_prs:
            if issue_status == "closed":
                return (
                    False,
                    f"PROTOCOL VIOLATION: Issue '{issue_id}' is CLOSED but PR #{open_prs[0]['number']} is still OPEN. "
                    f"Issues must remain open (status/label: 'in_review') until their PR is merged.",
                )
            if not is_in_review:
                return (
                    False,
                    f"PROTOCOL VIOLATION: PR #{open_prs[0]['number']} is OPEN. "
                    f"Please update issue '{issue_id}' status or labels to 'in_review' (bd update {issue_id} --add-label in_review).",
                )

        return True, "Issue closure state aligned with PR status"

    except Exception as e:
        return False, f"Closure gate check error: {e}"


def check_workspace_cleanup() -> tuple[bool, str]:
    """Verify that the workspace is free of temporary session artifacts drift."""
    try:
        # Check for untracked files using git
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return True, "Could not check for untracked files (skipping)"

        untracked = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Standard session files that are allowed in root during execution but should be noted
        allowed_in_root = ["task.md", "debrief.md", ".reflection_input.json"]

        drift = [f for f in untracked if f not in allowed_in_root and not f.startswith("tests/")]

        if not drift:
            return True, "Workspace clean of temporary artifact drift"

        # Check for specifically suspicious prefixes/suffixes
        suspicious = [
            f
            for f in drift
            if any(pattern in f for pattern in [".bak", ".tmp", "copy", "old", "test_"])
        ]

        if suspicious:
            return (
                False,
                f"Suspicious temporary files detected: {', '.join(suspicious)}. Please clean up before finalization.",
            )

        # Non-suspicious but untracked files - just a warning
        return (
            True,
            f"Workspace has {len(drift)} untracked files (e.g., {drift[0]}). Ensure these are intended to be part of the PR.",
        )

    except Exception as e:
        return False, f"Workspace cleanup check error: {e}"


def inject_debrief_to_beads(*args) -> tuple[bool, str]:
    """Inject content from debrief.md into Beads issue comments."""
    issue_id = get_active_issue_id()
    if not issue_id:
        return True, "No active issue identified (skipping injection)"

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if not brain_dir.exists():
        return True, "No brain directory found (skipping injection)"

    session_dirs = sorted(
        [d for d in brain_dir.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )[:1]

    if not session_dirs:
        return True, "No recent session found (skipping injection)"

    debrief_path = session_dirs[0] / "debrief.md"
    if not debrief_path.exists():
        return True, "No debrief.md found in recent session (skipping injection)"

    content = debrief_path.read_text()

    # Check if we should only inject 'Implementation Details'
    if "## Implementation Details" in content:
        parts = content.split("## Implementation Details")
        if len(parts) > 1:
            # Take everything after Implementation Details, up to the next header or end
            injection_content = parts[1].split("\n#")[0].strip()
        else:
            injection_content = content.strip()
    else:
        injection_content = content.strip()

    if not injection_content:
        return True, "No content found in debrief.md to inject"

    # Check for duplicates by querying beads
    try:
        show_res = subprocess.run(
            ["bd", "show", issue_id], capture_output=True, text=True, timeout=10
        )
        if show_res.returncode == 0:
            # Use a smaller snippet to check for existence to avoid match failures due to truncation or headers
            snippet = injection_content[:200]
            if snippet in show_res.stdout:
                return True, f"Debrief content already exists in issue '{issue_id}' comments."
    except Exception:
        pass

    # Inject using bd comments add
    try:
        # We'll use a temporary file to avoid shell expansion issues with large content
        temp_debrief = Path("/tmp/debrief_to_inject.md")
        temp_debrief.write_text(injection_content)

        result = subprocess.run(
            ["bd", "comments", "add", issue_id, "-f", str(temp_debrief)],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if temp_debrief.exists():
            temp_debrief.unlink()

        if result.returncode == 0:
            return True, f"Injected debrief content into issue '{issue_id}'"
        else:
            return False, f"Failed to inject debrief: {result.stderr.strip()}"
    except Exception as e:
        return False, f"Error during debrief injection: {e}"


def check_protocol_compliance_reporting() -> tuple[bool, str]:
    """Verify that the session debrief contains the mandatory protocol compliance statement with Beads ID and 🏁."""
    issue_id = get_active_issue_id()
    if not issue_id:
        return False, "Could not determine active Beads issue ID for compliance reporting"

    target_pattern = (
        rf"Protocol Compliance: 100% verified via Orchestrator\s+\({re.escape(issue_id)}\)\.?\s*🏁"
    )

    # Potential debrief locations
    debrief_paths = [Path("debrief.md")]

    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for d in session_dirs:
            debrief_paths.append(d / "debrief.md")

    for debrief_path in debrief_paths:
        if debrief_path.exists():
            try:
                content = debrief_path.read_text()
                if re.search(target_pattern, content):
                    return True, f"Full protocol compliance reporting found in {debrief_path}"
                elif "Protocol Compliance: 100% verified via Orchestrator." in content:
                    return (
                        False,
                        f"Compliance statement found in {debrief_path} but missing issue ID '{issue_id}' or 🏁. Expected: 'Protocol Compliance: 100% verified via Orchestrator ({issue_id}) 🏁'",
                    )
            except Exception:
                pass

    return (
        False,
        f"Missing required compliance statement: 'Protocol Compliance: 100% verified via Orchestrator ({issue_id}) 🏁'",
    )
