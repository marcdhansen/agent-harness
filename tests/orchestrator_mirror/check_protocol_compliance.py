"""
Orchestrator - Agent Workflow Coordinator

Verifies SOP compliance at each phase (Initialization, Finalization) and validates that agents
complete each step adequately and invoke appropriate skills.

Usage:
    python check_protocol_compliance.py --init     # Initialization validation
    python check_protocol_compliance.py --finalize # Finalization validation
    python check_protocol_compliance.py --status   # Full orchestration status
    python check_protocol_compliance.py --help     # Show help
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Add universal scripts to path
sys.path.append(str(Path.home() / ".agent/scripts"))
sys.path.append(str(Path.home() / ".agent/ledgers"))

# Import modular validators
try:
    from validators.code_validator import validate_tdd_compliance
    from validators.common import (
        Colors,
        check_mark,
        check_tool_available,
        check_tool_version,
        warning_mark,
    )
    from validators.finalization_validator import (
        check_beads_pr_sync,
        check_child_pr_linkage,
        check_code_review_status,
        check_debriefing_invoked,
        # check_handoff_beads_id,
        check_handoff_compliance,
        check_handoff_pr_link,
        check_handoff_pr_verification,
        # check_issue_closure_gate,
        check_linked_repositories,
        check_no_separate_review_issues,
        # check_no_wip_files,
        check_pr_decomposition_closure,
        check_pr_exists,
        check_progress_log_exists,
        # check_protocol_compliance_reporting,
        check_reflection_invoked,
        check_todo_completion,
        check_workspace_cleanup,
    )

    # check_wrapup_exclusivity,
    # check_wrapup_indicator_symmetry,
    # inject_debrief_to_beads,
    from validators.git_validator import (
        check_branch_info,
        check_branch_issue_coupling,
        check_closed_issue_branches,
        check_git_status,
        check_rebase_status,
        check_sop_infrastructure_changes,
        check_workspace_integrity,
        get_active_issue_id,
        prune_local_branches,
        validate_atomic_commits,
    )
    from validators.plan_validator import (
        check_beads_issue,
        check_hook_integrity,
        check_plan_approval,
        check_planning_docs,
        check_sop_simplification,
    )
    # from validators.session_validator import check_harness_session
except ImportError as e:
    print(f"Warning: Could not import modular validators: {e}")
    pass


def load_json_checklist(phase_name: str) -> dict | None:
    """Load SOP checklist from workspace JSON."""
    config_path = Path.cwd() / ".agent" / "rules" / "checklists" / f"{phase_name}.json"
    paths = [
        config_path,
        Path(".agent/rules/checklists") / f"{phase_name}.json",
        Path(".agent/checklists") / f"{phase_name}.json",
    ]
    for path in paths:
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
    return None


def run_phase_from_json(
    phase_name: str, verbose: bool = False
) -> tuple[bool, list[str], list[str]]:
    """Run a checklist phase defined in JSON."""
    data = load_json_checklist(phase_name)
    if not data or "phases" not in data or not data["phases"]:
        return False, [], []

    phase = data["phases"][0]
    print(f"{Colors.BOLD}📋 {phase['name'].upper()} (JSON-Driven){Colors.END}")
    print("=" * 40)
    if phase.get("description"):
        print(f"{phase['description']}")
    print()

    blockers = []
    warnings = []

    for check in phase.get("checks", []):
        validator_name = check["validator"]
        # Get function from global or imported scope
        # First check globals, then check imported validator modules if needed
        validator = globals().get(validator_name)

        if not validator:
            print(
                f"├── {check['id']}: {Colors.RED}❌{Colors.END} Validator '{validator_name}' not found"
            )
            blockers.append(f"Missing validator: {validator_name}")
            continue

        try:
            args = check.get("args", [])
            processed_args = []
            for arg in args:
                try:
                    processed_args.append(int(arg))
                except (ValueError, TypeError):
                    processed_args.append(arg)

            result = validator(*processed_args)
            if isinstance(result, tuple) and len(result) == 2:
                if isinstance(result[1], bool):
                    passed = result[1]
                    msg = f"Branch: {result[0]}"
                else:
                    passed = result[0]
                    msg = result[1]

                if isinstance(msg, list):
                    if not msg:
                        msg = "verified"
                    else:
                        msg = f"found items: {', '.join(map(str, msg))}"
            else:
                passed = bool(result)
                msg = "Check passed" if passed else "Check failed"

            icon = check_mark(passed)
            print(f"├── {check['description']}: {icon} {msg}")

            if not passed:
                if check["type"] == "BLOCKER":
                    blockers.append(f"{check['description']}: {msg}")
                else:
                    warnings.append(f"{check['description']}: {msg}")
        except Exception as e:
            print(f"├── {check['description']}: {Colors.RED}❌{Colors.END} Error: {e}")
            blockers.append(f"Validator error ({validator_name}): {e}")

    print()
    return True, blockers, warnings


def update_progress_ledger(phase: str, status: str, result: str):
    """Update the Progress Ledger with phase result."""
    manager = Path.home() / ".agent/ledgers/ledger-manager.py"
    if manager.exists():
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(manager),
                    "add-step",
                    "harness",
                    f"Phase: {phase}",
                    result,
                    "--status",
                    status,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception:
            pass


try:
    from compliance_validators import validate_initialization
except ImportError:
    validate_initialization = None


def run_initialization(verbose: bool = False) -> bool:
    """Run Initialization validation."""
    # Ensure session is initialized BEFORE running checklist if we have an active ID
    active_id = get_active_issue_id()
    if active_id:
        try:
            session_dir = Path.cwd() / ".agent" / "sessions"
            session_dir.mkdir(parents=True, exist_ok=True)
            session_file = session_dir / "session.lock"

            if not session_file.exists():
                session_data = {
                    "id": f"sess_{int(datetime.now().timestamp())}",
                    "mode": "full",
                    "issue_id": active_id,
                    "started_at": datetime.now().timestamp(),
                    "status": "active",
                }
                session_file.write_text(json.dumps(session_data))
                print(f"├── Session Tracking: ✅ Initialized {session_data['id']}")
        except Exception as e:
            print(f"├── Session Tracking: ⚠️ Failed to initialize: {e}")

    # Try JSON-driven approach
    executed, blockers, warnings = run_phase_from_json("initialization", verbose)
    if executed:
        if blockers:
            print(f"{Colors.RED}{Colors.BOLD}❌ INITIALIZATION BLOCKED (JSON){Colors.END}")
            for blocker in blockers:
                print(f"  - {blocker}")
            update_progress_ledger("Initialization", "failure", f"Blocked: {blockers}")
            return False

        print(f"{Colors.GREEN}{Colors.BOLD}✅ INITIALIZATION COMPLETE (JSON){Colors.END}")
        update_progress_ledger("Initialization", "success", "Clean JSON initialization complete")
        return True

    # Fallback to legacy hardcoded logic
    print(f"{Colors.BOLD}📋 INITIALIZATION CHECK (Legacy){Colors.END}")
    print("=" * 40)
    print()

    blockers = []
    warnings = []

    # Tool Check
    required_tools = [
        ("git", "2.25.0", "--version"),
        ("bd", "0.40.0", "version"),
    ]
    optional_tools = [
        ("uv", "0.5.0", "--version"),
        ("python3", "3.10.0", "--version"),
    ]

    tools_ok = True
    tool_details = []
    for tool, min_v, flag in required_tools:
        ok, msg = check_tool_version(tool, min_v, flag)
        if not ok:
            tools_ok = False
            blockers.append(msg)
        tool_details.append((tool, ok, msg))

    print(f"├── Tools: {check_mark(tools_ok)} ", end="")
    if tools_ok:
        print("Required tools version check passed")
    else:
        print("Tool version requirements not met")

    if verbose or not tools_ok:
        for tool, ok, msg in tool_details:
            print(f"│   └── {tool}: {check_mark(ok)} {msg}")

    # Optional tool warnings
    for tool, min_v, flag in optional_tools:
        ok, msg = check_tool_version(tool, min_v, flag)
        if not ok:
            warnings.append(f"Optional tool {msg}")

    # Workspace Integrity Check
    integrity_ok, missing_paths = check_workspace_integrity()
    print(f"├── Integrity: {check_mark(integrity_ok)} ", end="")
    if integrity_ok:
        print("Workspace integrity verified")
    else:
        print(f"Missing mandatory components: {missing_paths}")
        blockers.append(f"Workspace integrity failure: Missing {missing_paths}")

    # Rebase Status Check
    rebase_ok, rebase_msg = check_rebase_status()
    print(f"├── Rebase Status: {check_mark(rebase_ok)} {rebase_msg}")
    if not rebase_ok:
        blockers.append(rebase_msg)

    # Git Status Check
    git_ok, git_msg = check_git_status()
    print(f"├── Git Clean: {check_mark(git_ok)} {git_msg.split(chr(10))[0]}")
    if not git_ok:
        # Warning only for init
        warnings.append(f"Uncommitted changes: {git_msg}")

    # Stale Branches Check
    closed_ok, closed_msg = check_closed_issue_branches()
    prune_ok, prune_msg = prune_local_branches(dry_run=True)
    if not closed_ok or not prune_ok:
        print(f"├── Stale Branches: {warning_mark()} Stale branches detected")
        if not closed_ok:
            warnings.append(closed_msg)
        if not prune_ok:
            warnings.append(prune_msg)
    else:
        print(f"├── Stale Branches: {check_mark(True)} No stale branches detected")

    # Context Check
    docs_ok, missing_docs = check_planning_docs()
    print(f"├── Context: {check_mark(docs_ok)} ", end="")
    if docs_ok:
        print("Planning documents accessible")
    else:
        print(f"Missing: {missing_docs}")
        blockers.append(f"Planning documents missing: {missing_docs}")

    # Issue Check (Optional for Init)
    issues_ok, issues_msg = check_beads_issue()
    issue_icon = check_mark(issues_ok) if issues_ok else f"{Colors.BLUE}ℹ️{Colors.END}"
    print(f"├── Issues: {issue_icon} {issues_msg} (Optional for planning)")
    # No warning/blocker for missing issues during initialization

    # Branch-Issue Coupling Check
    coupling_ok, coupling_msg = check_branch_issue_coupling()
    print(f"├── Branch-Issue Coupling: {check_mark(coupling_ok)} {coupling_msg}")
    if not coupling_ok:
        blockers.append(coupling_msg)

    # SOP Modification/Simplification Check
    simplification_ok, simplification_msg = check_sop_simplification()
    print(f"├── Simplification: {check_mark(simplification_ok)} {simplification_msg}")
    if not simplification_ok:
        warnings.append(simplification_msg)

    # SOP Gate Change Check
    sop_mod_script = (
        Path.home() / ".gemini/antigravity/skills/sop-modification/scripts/validate_sop_change.py"
    )
    if sop_mod_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(sop_mod_script)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            sop_ok = result.returncode == 0
            sop_msg = result.stdout.strip() or result.stderr.strip()
            first_line = "No issues" if not sop_msg else sop_msg.split("\n")[0]
            print(f"├── SOP Gates: {check_mark(sop_ok)} {first_line}")
            if not sop_ok:
                blockers.append(f"SOP gate violation: {sop_msg}")
        except Exception as e:
            print(f"├── SOP Gates: {warning_mark()} Error checking SOP gates: {e}")

    # Plan Approval Check
    approval_ok, approval_msg = check_plan_approval()
    # Progress Log Check
    progress_ok, progress_msg = check_progress_log_exists()
    print(f"├── Progress Log: {check_mark(progress_ok)} {progress_msg}")

    print(f"└── Approval: {check_mark(approval_ok)} {approval_msg}")
    if not approval_ok:
        blockers.append(approval_msg)
    if not progress_ok:
        warnings.append("Progress log missing - run /log-progress to initialize context")

    print()

    # Summary
    if blockers:
        print(f"{Colors.RED}{Colors.BOLD}❌ INITIALIZATION BLOCKED{Colors.END}")
        print()
        print("BLOCKERS:")
        for i, blocker in enumerate(blockers, 1):
            print(f"  {i}. {blocker}")
        update_progress_ledger("Initialization", "failure", f"Blocked: {blockers}")
        return False
    elif warnings:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ INITIALIZATION PASSED WITH WARNINGS{Colors.END}")
        print()
        print("WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print()
        print("Ready for execution (address warnings when possible)")
        update_progress_ledger("Initialization", "success", f"Passed with warnings: {warnings}")
        return True
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ INITIALIZATION COMPLETE{Colors.END}")
        print()
        print("Ready for execution!")
        update_progress_ledger("Initialization", "success", "Clean initialization complete")
        return True


def run_turbo_initialization(verbose: bool = False) -> bool:
    """Run lightweight Turbo Mode initialization validation."""
    print(f"{Colors.BOLD}⚡ TURBO INITIALIZATION (Turbo Create Protocol){Colors.END}")
    print("=" * 40)
    print("Turbo Mode: Administrative/Metadata tasks only.")
    print("Guidelines: No code changes, no full planning required.")
    print()

    blockers = []
    warnings = []

    # Tool Check (Only Git is strictly required for Turbo)
    git_ok = check_tool_available("git")
    print(f"├── Git: {check_mark(git_ok)}")

    # Check for existing code blockers (should not have uncommitted code changes)
    git_clean, git_msg = check_git_status(turbo=True)
    print(f"├── Git Clean: {check_mark(git_clean)} {git_msg.split(chr(10))[0]}")
    if not git_clean:
        blockers.append(git_msg)

    # Rebase Status Check
    rebase_ok, rebase_msg = check_rebase_status()
    print(f"├── Rebase Status: {check_mark(rebase_ok)} {rebase_msg}")
    if not rebase_ok:
        blockers.append(rebase_msg)

    # Stale Branches Check
    closed_ok, closed_msg = check_closed_issue_branches()
    prune_ok, prune_msg = prune_local_branches(dry_run=True)
    if not closed_ok or not prune_ok:
        print(f"├── Stale Branches: {warning_mark()} Stale branches detected")
        if not closed_ok:
            warnings.append(closed_msg)
        if not prune_ok:
            warnings.append(prune_msg)
    else:
        print(f"├── Stale Branches: {check_mark(True)} No stale branches detected")

    # Check for SOP infrastructure changes (requires Full Mode)
    sop_infra_escalation, sop_infra_msg = check_sop_infrastructure_changes()
    sop_infra_icon = warning_mark() if sop_infra_escalation else check_mark(True)
    print(f"├── SOP Infrastructure: {sop_infra_icon} {sop_infra_msg.split(chr(10))[0]}")

    # Branch-Issue Coupling Check (Harden Turbo Mode)
    coupling_ok, coupling_msg = check_branch_issue_coupling()
    print(f"└── Branch-Issue Coupling: {check_mark(coupling_ok)} {coupling_msg}")

    print()
    if not git_ok or not git_clean or sop_infra_escalation or not coupling_ok:
        print(f"{Colors.RED}{Colors.BOLD}❌ TURBO BLOCKED{Colors.END}")
        if not git_clean:
            print(f"  {warning_mark()} Code changes detected. Escalate to Full SOP (--init).")
        if sop_infra_escalation:
            print(
                f"  {warning_mark()} SOP infrastructure changes detected. Full Mode REQUIRED (--init)."
            )
        if not coupling_ok:
            print(f"  {warning_mark()} Branch-Issue Coupling failure: {coupling_msg}")
        return False

    print(f"{Colors.GREEN}{Colors.BOLD}✅ TURBO READY{Colors.END}")
    print("Ready for administrative tasks (bd create, docs, research).")
    return True


def run_execution(verbose: bool = False) -> bool:
    """Run Execution Phase status check."""
    # Try JSON-driven approach first
    executed, blockers, warnings = run_phase_from_json("execution", verbose)
    if executed:
        if blockers:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ EXECUTION SETUP INCOMPLETE (JSON){Colors.END}")
            return False
        print(f"{Colors.GREEN}{Colors.BOLD}✅ EXECUTION ACTIVE (JSON){Colors.END}")
        return True

    # Fallback to legacy hardcoded logic
    print(f"{Colors.BOLD}🚀 EXECUTION PHASE (Legacy){Colors.END}")
    print("=" * 40)
    print()
    print("Execution: Active work phase - executing the task.")
    print()

    issues = []

    # Check we're on a feature branch (should be working, not on main)
    branch, is_feature = check_branch_info()
    print(f"├── Branch: {check_mark(is_feature)} ", end="")
    if is_feature:
        print(f"Working on {branch}")
    else:
        print(f"On {branch} (should be feature branch)")
        issues.append("Create a feature branch before starting work")

    # Check task.md exists in brain directory
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    task_found = False
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for session_dir in session_dirs:
            if (session_dir / "task.md").exists():
                task_found = True
                break

    print(f"├── Task Tracked: {check_mark(task_found)} ", end="")
    if task_found:
        print("task.md found")
    else:
        print("No task.md found")
        issues.append("Create task.md to track work")

    # MANDATORY Beads Issue Check for Execution
    issues_ok, issues_msg = check_beads_issue()
    print(f"├── Beads Issue: {check_mark(issues_ok)} {issues_msg}")
    if not issues_ok:
        issues.append("MANDATORY: Current rule requires a Beads issue before implementation")

    # MANDATORY Plan Approval Check for Execution
    approval_ok, approval_msg = check_plan_approval()
    print(f"├── Plan Approval: {check_mark(approval_ok)} {approval_msg}")
    if not approval_ok:
        issues.append(
            f"MANDATORY: {approval_msg}. Approval required in task.md before implementation."
        )

    # MANDATORY TDD Compliance Check
    tdd_ok, tdd_msg = validate_tdd_compliance()
    print(f"├── TDD Compliance: {check_mark(tdd_ok)} {tdd_msg}")
    if not tdd_ok:
        issues.append(tdd_msg)

    # Git status - during Execution, uncommitted changes are expected
    git_ok, git_msg = check_git_status()
    print("└── Git Status: ", end="")
    if git_ok:
        print(f"{Colors.BLUE}ℹ️{Colors.END} Clean (no changes yet)")
    else:
        print(f"{Colors.BLUE}ℹ️{Colors.END} Work in progress")

    print()

    # Execution Guidelines
    print(f"{Colors.BOLD}Execution Guidelines:{Colors.END}")
    print("  • Follow Spec-Driven TDD: Red → Green → Refactor")
    print("  • Update task.md as you complete items")
    print("  • Commit frequently with clear messages")
    print("  • Run quality gates before Finalization")
    print()

    if issues:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ EXECUTION SETUP INCOMPLETE{Colors.END}")
        print()
        print("SETUP NEEDED:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ EXECUTION ACTIVE{Colors.END}")
        print()
        print("Execute the task. Run --finalize when ready to land.")
        return True


def run_finalization(verbose: bool = False) -> bool:
    """Run Finalization validation."""
    # Try JSON-driven approach first
    executed, blockers, warnings = run_phase_from_json("finalization", verbose)
    if executed:
        if blockers:
            print(f"{Colors.RED}{Colors.BOLD}❌ FINALIZATION BLOCKED (JSON){Colors.END}")
            for blocker in blockers:
                print(f"  - {blocker}")
            update_progress_ledger("Finalization", "failure", f"Blocked: {blockers}")
            return False

        print(f"{Colors.GREEN}{Colors.BOLD}✅ FINALIZATION COMPLETE (JSON){Colors.END}")
        update_progress_ledger("Finalization", "success", "Clean JSON finalization complete")
        return True

    # Fallback to legacy hardcoded logic
    print(f"{Colors.BOLD}🛬 FINALIZATION CHECK (Legacy){Colors.END}")
    print("=" * 40)
    print()
    print("Finalization focuses on safe landing: code quality, clean git, successful push.")
    print()

    blockers = []
    warnings = []

    # Git Status Check
    git_ok, git_msg = check_git_status()
    print(f"├── Git Status: {check_mark(git_ok)} {git_msg.split(chr(10))[0]}")
    if not git_ok:
        blockers.append(git_msg)

    # Branch Info
    branch, is_feature = check_branch_info()
    branch_icon = check_mark(is_feature) if is_feature else warning_mark()
    print(f"├── Branch: {branch_icon} {branch}")
    if not is_feature and branch not in ["main", "master"]:
        warnings.append(f"Not on a feature branch: {branch}")

    # SOP Simplification Check
    simplification_ok, simplification_msg = check_sop_simplification()
    print(f"├── Simplification: {check_mark(simplification_ok)} {simplification_msg}")
    if not simplification_ok:
        warnings.append(simplification_msg)

    # Hand-off Compliance Check (for multi-phase implementations)
    handoff_ok, handoff_msg = check_handoff_compliance()
    handoff_icon = check_mark(handoff_ok) if handoff_ok else warning_mark()
    print(f"├── Hand-offs: {handoff_icon} {handoff_msg}")
    if not handoff_ok and "not a multi-phase implementation" not in handoff_msg:
        blockers.append("Hand-off compliance failed - run verify_handoff_compliance.sh")

    # Atomic Commit Validation (SOP git-workflow requirement)
    atomic_ok, atomic_errors = validate_atomic_commits()
    print(f"├── Atomic Commits: {check_mark(atomic_ok)} ", end="")
    if atomic_ok:
        print("Single atomic commit verified")
    else:
        print("Validation failed")
        for error in atomic_errors:
            print(f"│   └── {error}")
        blockers.extend(atomic_errors)

    # Reflection Check (Enforced at Finalization to ensure it's not skipped)
    reflect_ok, reflect_msg = check_reflection_invoked()
    print(f"├── Reflection: {check_mark(reflect_ok)} {reflect_msg}")
    if not reflect_ok:
        blockers.append("Reflection not captured - invoke /reflect (Mandatory for Finalization)")

    # Linked Repository Validation
    linked_ok, linked_errors = check_linked_repositories()
    linked_icon = check_mark(linked_ok) if linked_ok else warning_mark()
    print(f"├── Linked Repos: {linked_icon} ", end="")
    if linked_ok:
        print("All linked repositories compliant")
    else:
        print("Validation failed")
        for error in linked_errors:
            print(f"│   └── {error}")
        blockers.extend(linked_errors)

    # Code Review Check (NEW MANDATORY GATE)
    review_ok, review_msg = check_code_review_status()
    print(f"├── Code Review: {check_mark(review_ok)} {review_msg}")
    if not review_ok:
        blockers.append(f"Code Review failure: {review_msg} - run /code-review")

    # Prohibition of Separate Review Issues
    pr_review_ok, pr_review_msg = check_no_separate_review_issues()
    print(f"├── No Separate Review Issues: {check_mark(pr_review_ok)} {pr_review_msg}")
    if not pr_review_ok:
        blockers.append(pr_review_msg)

    # PR Existence Check (MANDATORY for code changes)
    pr_ok, pr_msg = check_pr_exists()
    print(f"├── PR Created: {check_mark(pr_ok)} {pr_msg}")
    if not pr_ok:
        blockers.append(f"PR required for code changes: {pr_msg}")

    # Todo Completion Check (Sisyphus pattern)
    todo_ok, todo_msg = check_todo_completion()
    print(f"├── Todo Enforcer: {check_mark(todo_ok)} {todo_msg}")
    if not todo_ok:
        blockers.append(f"Todo Enforcer failed: {todo_msg}")

    # Hook Integrity Check (NEW MANDATORY GATE)
    hook_ok, hook_msg = check_hook_integrity()
    print(f"├── Hook Integrity: {check_mark(hook_ok)} {hook_msg}")
    if not hook_ok:
        blockers.append(f"Hook integrity failure: {hook_msg} - hooks may have been tampered with")

    # PR Decomposition Closure Check (PR Response Protocol)
    decomp_ok, decomp_msg = check_pr_decomposition_closure()
    print(f"├── PR Decomposition: {check_mark(decomp_ok)} {decomp_msg}")
    if not decomp_ok:
        blockers.append(f"PR Response Protocol violation: {decomp_msg}")

    # Child PR Linkage Check (PR Response Protocol)
    linkage_ok, linkage_msg = check_child_pr_linkage()
    print(f"├── Child PR Linkage: {check_mark(linkage_ok)} {linkage_msg}")
    if not linkage_ok:
        blockers.append(f"PR Response Protocol violation: {linkage_msg}")

    # Handoff PR Verification (Orphaned PR prevention)
    handoff_pr_v_ok, handoff_pr_v_msg = check_handoff_pr_verification()
    print(f"├── Handoff PR Verification: {check_mark(handoff_pr_v_ok)} {handoff_pr_v_msg}")
    if not handoff_pr_v_ok:
        blockers.append(f"Handoff PR verification failure: {handoff_pr_v_msg}")

    # Beads-PR Synchronization Check
    beads_pr_ok, beads_pr_msg = check_beads_pr_sync()
    print(f"├── Beads-PR Sync: {check_mark(beads_pr_ok)} {beads_pr_msg}")
    if not beads_pr_ok:
        blockers.append(f"Beads-PR sync failure: {beads_pr_msg}")

    # Local Branch Cleanup Check (Stale branch detection)
    stale_branches_ok, stale_msg = prune_local_branches(dry_run=True)
    print(f"├── Stale Branches: {check_mark(stale_branches_ok)} {stale_msg}")
    if not stale_branches_ok:
        blockers.append(stale_msg)

    # Workspace Cleanup Check (Temporary artifact drift detection)
    cleanup_ok, cleanup_msg = check_workspace_cleanup()
    print(f"└── Workspace Cleanup: {check_mark(cleanup_ok)} {cleanup_msg}")
    if not cleanup_ok:
        blockers.append(f"Workspace cleanup failure: {cleanup_msg}")

    print()

    # Summary
    if blockers:
        print(f"{Colors.RED}{Colors.BOLD}❌ FINALIZATION BLOCKED{Colors.END}")
        print()
        print("BLOCKERS:")
        for i, blocker in enumerate(blockers, 1):
            print(f"  {i}. {blocker}")
        print()
        print("Resolve blockers before completing Finalization.")
        update_progress_ledger("Finalization", "failure", f"Blocked: {blockers}")
        return False
    elif warnings:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ FINALIZATION PASSED WITH WARNINGS{Colors.END}")
        print()
        print("WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print()
        print("Safe landing! Now proceed to Retrospective.")
        update_progress_ledger("Finalization", "success", f"Passed with warnings: {warnings}")
        return True
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ FINALIZATION COMPLETE{Colors.END}")
        print()
        print("Safe landing! Now proceed to Retrospective.")
        update_progress_ledger("Finalization", "success", "Clean Finalization complete")
        return True


def run_turbo_finalization(verbose: bool = False) -> bool:
    """Run lightweight Turbo Mode finalization validation."""
    print(f"{Colors.BOLD}⚡ TURBO FINALIZATION{Colors.END}")
    print("=" * 40)
    print()

    # Git Status Check (Strict: No uncommitted changes allowed in Finalization)
    git_ok, git_msg = check_git_status(turbo=False)
    print(f"├── Git Status: {check_mark(git_ok)} {git_msg.split(chr(10))[0]}")

    # Beads Sync check (Optional but recommended)
    bd_ok = check_tool_available("bd")
    print(
        f"└── Beads Sync: {check_mark(bd_ok) if bd_ok else warning_mark()} {'Available' if bd_ok else 'Missing'}"
    )

    print()
    if not git_ok:
        print(f"{Colors.RED}{Colors.BOLD}❌ TURBO FINALIZATION BLOCKED{Colors.END}")
        print(f"Error: {git_msg}")
        return False

    print(f"{Colors.GREEN}{Colors.BOLD}✅ TURBO FINALIZATION COMPLETE{Colors.END}")
    return True


def run_retrospective(verbose: bool = False) -> bool:
    """Run Retrospective validation."""
    # Try JSON-driven approach first
    executed, blockers, warnings = run_phase_from_json("retrospective", verbose)
    if executed:
        if blockers:
            print(f"{Colors.RED}{Colors.BOLD}❌ RETROSPECTIVE INCOMPLETE (JSON){Colors.END}")
            return False
        if warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ RETROSPECTIVE INCOMPLETE (JSON){Colors.END}")
            return False
        print(f"{Colors.GREEN}{Colors.BOLD}✅ RETROSPECTIVE COMPLETE (JSON){Colors.END}")
        return True

    # Fallback to legacy hardcoded logic
    print(f"{Colors.BOLD}🎖️ RETROSPECTIVE CHECK (Legacy){Colors.END}")
    print("=" * 40)
    print()
    print("Retrospective: strategic learning and session closure.")
    print()

    blockers = []
    warnings = []

    # Reflection Check
    reflect_ok, reflect_msg = check_reflection_invoked()
    print(f"├── Reflection: {check_mark(reflect_ok)} {reflect_msg}")
    if not reflect_ok:
        blockers.append("Reflection not captured - invoke /reflect (Mandatory)")

    # Debriefing Check
    debrief_ok, debrief_msg = check_debriefing_invoked()
    print(f"├── Debrief File: {check_mark(debrief_ok)} {debrief_msg}")
    if not debrief_ok:
        blockers.append("Debrief file not generated - run mission_debriefing.py (Mandatory)")

    # Plan Approval Cleared Check
    approval_ok, approval_msg = check_plan_approval()
    # For debrief, we WANT approval to be stale/missing (means it was cleared)
    approval_cleared = not approval_ok or "stale" in approval_msg.lower()
    print(f"├── Plan Cleared: {check_mark(approval_cleared)} ", end="")
    if approval_cleared:
        print("Plan approval cleared or stale")
    else:
        print(f"Plan still active: {approval_msg}")
        blockers.append("Clear the ## Approval marker in task.md (Mandatory)")

    # Progress Log Reflector Synthesis Check
    log_ok, log_msg = check_progress_log_exists()
    reflector_ok = False
    reflector_msg = "Progress log missing"
    if log_ok:
        try:
            issue_id = get_active_issue_id()
            log_path = Path.home() / ".agent/progress-logs" / f"{issue_id}.md"
            content = log_path.read_text()
            if "Reflector Synthesis" in content:
                parts = content.split("Reflector Synthesis")
                if len(parts) > 1:
                    # Skip the first line which might be the remainder of the heading
                    section_lines = parts[1].split("\n")[1:]
                    if any(
                        line.strip() and not line.strip().startswith(("#", "!", "<!--"))
                        for line in section_lines
                    ):
                        reflector_ok = True
                        reflector_msg = "Reflector synthesis captured in progress log"
                    else:
                        reflector_msg = "Reflector synthesis empty in progress log"
        except Exception as e:
            reflector_msg = f"Error checking reflector: {e}"

    print(f"├── Reflector: {check_mark(reflector_ok)} {reflector_msg}")
    if not reflector_ok:
        blockers.append(f"Retrospective incomplete: {reflector_msg}")

    # PR Link in Handoff Check
    handoff_pr_ok, handoff_pr_msg = check_handoff_pr_link()
    print(f"├── PR Link in Handoff: {check_mark(handoff_pr_ok)} {handoff_pr_msg}")
    if not handoff_pr_ok:
        # Check if we actually changed code (if we didn't, PR link might not be required)
        git_clean, _ = check_git_status()
        if not git_clean:
            blockers.append(f"PR Link required in handoff: {handoff_pr_msg}")

    # Todo Completion Check (Sisyphus pattern)
    todo_ok, todo_msg = check_todo_completion()
    print(f"└── Todo Enforcer: {check_mark(todo_ok)} {todo_msg}")
    if not todo_ok:
        blockers.append(f"Todo Enforcer failed: {todo_msg}")

    print()

    # Summary
    if blockers:
        print(f"{Colors.RED}{Colors.BOLD}❌ RETROSPECTIVE INCOMPLETE{Colors.END}")
        print()
        print("BLOCKERS:")
        for i, blocker in enumerate(blockers, 1):
            print(f"  {i}. {blocker}")
        return False
    elif warnings:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ RETROSPECTIVE INCOMPLETE{Colors.END}")
        print()
        print("MISSING:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print()
        print("Complete these steps, then run --clean for final check.")
        return False
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ RETROSPECTIVE COMPLETE{Colors.END}")
        print()
        print("Now run --clean for final repo verification.")
        return True


def run_clean_state(verbose: bool = False) -> bool:
    """Run Clean State validation (formerly Cleanup)."""
    # Try JSON-driven approach first
    executed, blockers, warnings = run_phase_from_json("clean_state", verbose)
    if executed:
        if blockers or warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ REPO NOT CLEAN (JSON){Colors.END}")
            return False
        print(f"{Colors.GREEN}{Colors.BOLD}✅ REPO IS CLEAN (JSON){Colors.END}")
        return True

    # Fallback to legacy hardcoded logic
    print(f"{Colors.BOLD}✨ CLEAN STATE CHECK (Legacy){Colors.END}")
    print("=" * 40)
    print()
    print("Final verification: repo should be clean after PR merge.")
    print()

    issues = []
    # Automated Pruning
    prune_ok, prune_msg = prune_local_branches()
    print(f"├── Branch Pruning: {check_mark(prune_ok)} {prune_msg}")
    if not prune_ok:
        issues.append(prune_msg)

    # Branch Check
    branch, is_feature = check_branch_info()
    on_main = branch in ["main", "master"]
    print(f"├── Branch: {check_mark(on_main)} ", end="")
    if on_main:
        print(f"On {branch}")
    else:
        print(f"On {branch} (should be main)")
        issues.append(f"Merge PR and switch to main (currently on {branch})")

    # Git Status Check
    git_ok, git_msg = check_git_status()
    print(f"├── Git Clean: {check_mark(git_ok)} ", end="")
    if git_ok:
        print("Working tree clean")
    else:
        print("Uncommitted changes")
        issues.append("Commit and push remaining changes")

    # Up-to-date with remote
    up_to_date = True
    try:
        import subprocess

        result = subprocess.run(
            ["git", "status", "-uno"],
            capture_output=True,
            text=True,
        )
        if "behind" in result.stdout.lower():
            up_to_date = False
    except Exception:
        pass

    print(f"└── Synced: {check_mark(up_to_date)} ", end="")
    if up_to_date:
        print("Up to date with remote")
    else:
        print("Behind remote")
        issues.append("Pull latest changes from remote")

    # Artifact Cleanup Check
    temp_artifacts = (
        list(Path(".").glob("task.md"))
        + list(Path(".").glob("walkthrough.md"))
        + list(Path(".").glob("debrief.md"))
    )
    cleanup_ok = len(temp_artifacts) == 0
    print(f"\n├── Cleanup: {check_mark(cleanup_ok)} ", end="")
    if cleanup_ok:
        print("Temporary artifacts removed")
    else:
        print(f"Found temporary artifacts: {[f.name for f in temp_artifacts]}")
        issues.append(f"Remove temporary artifacts: {[f.name for f in temp_artifacts]}")

    print()

    # Summary
    if issues:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ REPO NOT CLEAN{Colors.END}")
        print()
        print("ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print()
        print("Resolve issues to achieve clean state.")
        return False
    else:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ REPO IS CLEAN{Colors.END}")
        print()
        print("Session complete. Ready for next mission!")
        return True


def run_summary(verbose: bool = False) -> bool:
    """Provide a concise SOP compliance summary for session handoffs."""
    print(f"{Colors.BOLD}📋 SOP COMPLIANCE SUMMARY{Colors.END}")
    print("=" * 40)

    # Initialization status
    init_ok, init_msg = check_plan_approval()
    # Finalization status
    git_ok, git_msg = check_git_status()
    # Retrospective status
    reflect_ok, _ = check_reflection_invoked()
    debrief_ok, _ = check_debriefing_invoked()

    # Higher-level phase status
    phases = [
        ("Initialization", init_ok),
        ("Execution", True),  # Implicit if we are at this stage
        ("Finalization", git_ok),
        ("Retrospective", reflect_ok and debrief_ok),
    ]

    for phase, ok in phases:
        print(f"{check_mark(ok)} {phase}")

    print("-" * 40)
    if all(ok for _, ok in phases):
        print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL PHASES COMPLIANT{Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️ COMPLIANCE PENDING{Colors.END}")

    return all(ok for _, ok in phases)


def run_status(verbose: bool = False) -> bool:
    """Show full orchestration status."""
    print(f"{Colors.BOLD}📊 ORCHESTRATOR STATUS{Colors.END}")
    print("=" * 40)
    print()

    # Current state
    branch, is_feature = check_branch_info()
    git_ok, _ = check_git_status()

    print(f"🌿 Branch: {branch}")
    print(f"📁 Git Clean: {'Yes' if git_ok else 'No'}")
    print()

    # Recent activity
    print("Recent Skill Status:")

    reflect_ok, reflect_msg = check_reflection_invoked()
    print(f"  - Reflect: {check_mark(reflect_ok)} {reflect_msg}")

    review_ok, review_msg = check_code_review_status()
    print(f"  - Code Review: {check_mark(review_ok)} {review_msg}")

    debrief_ok, debrief_msg = check_debriefing_invoked()
    print(f"  - Retrospective: {check_mark(debrief_ok)} {debrief_msg}")

    approval_ok, approval_msg = check_plan_approval()
    print(f"  - Plan Approval: {check_mark(approval_ok)} {approval_msg}")

    print()
    run_summary(verbose)
    print()
    print("Run --init, --execute, --finalize, or --retrospective for detailed phase checks.")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator - Agent Workflow Coordinator for SOP Compliance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run Initialization validation
    python check_protocol_compliance.py --init
    
    # Run Finalization check  
    python check_protocol_compliance.py --finalize
    
    # Show current status
    python check_protocol_compliance.py --status
    
    # Get concise compliance summary for handoff
    python check_protocol_compliance.py --summary
        """,
    )

    parser.add_argument(
        "--init",
        "--pfc",
        action="store_true",
        help="Run Initialization validation (formerly PFC)",
    )
    parser.add_argument(
        "--execute",
        "--ifo",
        action="store_true",
        help="Run Execution Phase status check (formerly IFO)",
    )
    parser.add_argument(
        "--finalize",
        "--rtb",
        action="store_true",
        help="Run Finalization validation",
    )
    parser.add_argument(
        "--retrospective",
        "--debrief",
        action="store_true",
        help="Run Retrospective validation (formerly Debrief)",
    )
    parser.add_argument(
        "--clean",
        "--cleanup",
        "--pristine",
        action="store_true",
        help="Run Clean State validation (formerly Cleanup)",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show full orchestration status",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Provide a concise SOP compliance summary for session handoffs",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run type-safe Pydantic validation and output JSON",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )
    parser.add_argument(
        "--turbo",
        action="store_true",
        help="Run in Turbo Mode (Turbo Create Protocol - lightweight validation)",
    )

    args = parser.parse_args()

    # Default to status if no option specified
    if not any(
        [
            args.init,
            args.execute,
            args.finalize,
            args.retrospective,
            args.clean,
            args.status,
            args.summary,
            args.validate,
        ]
    ):
        parser.print_help()
        sys.exit(0)

    success = True

    if args.validate:
        if validate_initialization:
            result = validate_initialization(Path.cwd())
            print(result.model_dump_json(indent=2))
            success = result.passed
        else:
            print("❌ Pydantic validators not available.")
            success = False
    elif args.init:
        if args.turbo:
            success = run_turbo_initialization(args.verbose)
        else:
            success = run_initialization(args.verbose)
    elif args.execute:
        success = run_execution(args.verbose)
    elif args.finalize:
        if args.turbo:
            success = run_turbo_finalization(args.verbose)
        else:
            success = run_finalization(args.verbose)
    elif args.retrospective:
        success = run_retrospective(args.verbose)
    elif args.clean:
        success = run_clean_state(args.verbose)
    elif args.status:
        success = run_status(args.verbose)
    elif args.summary:
        success = run_summary(args.verbose)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
