"""Tests for the Orchestrator's compliance checking logic."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the orchestrator script path to sys.path
# Add the orchestrator script path to sys.path
orchestrator_path = Path(__file__).parent / "orchestrator_mirror"
sys.path.insert(0, str(orchestrator_path))

# Import the functions to test
try:
    import check_protocol_compliance_mirror as orchestrator
except ImportError:
    # If the file is not directly importable as a module, we might need to mock sys.path differently
    # or the script might not be structured for easy import.
    # Let's hope it works, or we'll adjust.
    pass


class TestOrchestratorGitStatus(unittest.TestCase):
    """Test the check_git_status function."""

    @patch("subprocess.run")
    def test_git_status_clean(self, mock_run):
        """Test git status when working directory is clean."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_git_status(turbo=True)
        self.assertTrue(passed)
        self.assertEqual(msg, "Working directory clean")

    @patch("subprocess.run")
    def test_git_status_metadata_only(self, mock_run):
        """Test git status when only metadata files are changed."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M README.md\n M .agent-harness/task.md"
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_git_status(turbo=True)
        self.assertTrue(passed)
        self.assertIn("Documentation changes only (Turbo safe)", msg)

    @patch("subprocess.run")
    def test_git_status_code_change_escalation(self, mock_run):
        """Test git status when code files are changed in Turbo mode."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M src/main.py\n M tests/test_core.py"
        mock_run.value = (
            mock_result  # Wait, I used mock_run.value instead of return_value in thoughts
        )
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_git_status(turbo=True)
        self.assertFalse(passed)
        self.assertIn("ESCALATION REQUIRED", msg)
        self.assertIn("src/main.py", msg)

    @patch("subprocess.run")
    def test_git_status_mixed_changes_escalation(self, mock_run):
        """Test git status with both code and metadata changes."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M README.md\n M script.sh"
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_git_status(turbo=True)
        self.assertFalse(passed)
        self.assertIn("ESCALATION REQUIRED", msg)


class TestOrchestratorInitialization(unittest.TestCase):
    """Test the initialization checking functions."""

    @patch("check_protocol_compliance_mirror.check_tool_available")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.check_rebase_status")
    @patch("check_protocol_compliance_mirror.check_closed_issue_branches")
    @patch("check_protocol_compliance_mirror.prune_local_branches")
    @patch("check_protocol_compliance_mirror.check_sop_infrastructure_changes")
    @patch("check_protocol_compliance_mirror.check_branch_issue_coupling")
    def test_run_turbo_initialization_success(
        self, mock_coupling, mock_sop, mock_prune, mock_closed, mock_rebase, mock_git, mock_tool
    ):
        """Test successful Turbo initialization."""
        mock_tool.return_value = True
        mock_git.return_value = (True, "Working directory clean")
        mock_rebase.return_value = (True, "No hanging rebase")
        mock_closed.return_value = (True, "No closed issue branches")
        mock_prune.return_value = (True, "No stale branches")
        mock_sop.return_value = (False, "No SOP changes")
        mock_coupling.return_value = (True, "Coupling OK")

        with patch("builtins.print"):
            result = orchestrator.run_turbo_initialization()
        self.assertTrue(result)

    @patch("check_protocol_compliance_mirror.check_tool_available")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.check_rebase_status")
    @patch("check_protocol_compliance_mirror.check_closed_issue_branches")
    @patch("check_protocol_compliance_mirror.prune_local_branches")
    @patch("check_protocol_compliance_mirror.check_sop_infrastructure_changes")
    @patch("check_protocol_compliance_mirror.check_branch_issue_coupling")
    def test_run_turbo_initialization_blocked_by_code(
        self, mock_coupling, mock_sop, mock_prune, mock_closed, mock_rebase, mock_git, mock_tool
    ):
        """Test Turbo initialization blocked by code changes."""
        mock_tool.return_value = True
        mock_git.return_value = (False, "ESCALATION REQUIRED: Code changes detected")
        mock_rebase.return_value = (True, "No hanging rebase")
        mock_closed.return_value = (True, "No closed issue branches")
        mock_prune.return_value = (True, "No stale branches")
        mock_sop.return_value = (False, "No SOP changes")
        mock_coupling.return_value = (True, "Coupling OK")

        with patch("builtins.print"):
            result = orchestrator.run_turbo_initialization()
        self.assertFalse(result)


class TestOrchestratorExecution(unittest.TestCase):
    """Test the run_execution function."""

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.check_beads_issue")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.check_plan_approval")
    @patch("check_protocol_compliance_mirror.validate_tdd_compliance")
    @patch("check_protocol_compliance_mirror.Path")
    def test_run_execution_success(
        self, mock_path, mock_tdd, mock_approval, mock_git, mock_beads, mock_branch
    ):
        """Test successful execution phase validation."""
        mock_branch.return_value = ("agent-harness/test", True)
        mock_beads.return_value = (True, "Issues ready: 1")
        mock_git.return_value = (False, "Work in progress")  # IFO expects changes
        mock_approval.return_value = (True, "Plan approved")
        mock_tdd.return_value = (True, "TDD compliance verified")

        # Setup Path mocks
        mock_home = MagicMock()
        mock_path.home.return_value = mock_home

        mock_brain_dir = MagicMock()
        # Path.home() / ".gemini" / "antigravity" / "brain"
        # 1: / ".gemini" -> mock_home.__truediv__
        # 2: / "antigravity" -> return of 1.__truediv__
        # 3: / "brain" -> return of 2.__truediv__
        mock_h1 = MagicMock()
        mock_h2 = MagicMock()
        mock_home.__truediv__.return_value = mock_h1
        mock_h1.__truediv__.return_value = mock_h2
        mock_h2.__truediv__.return_value = mock_brain_dir

        mock_brain_dir.exists.return_value = True

        mock_session = MagicMock()
        mock_session.is_dir.return_value = True
        mock_session.stat.return_value.st_mtime = 123456789

        mock_brain_dir.iterdir.return_value = [mock_session]
        (mock_session / "task.md").exists.return_value = True

        with patch("builtins.print"):
            result = orchestrator.run_execution()
        self.assertTrue(result)

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.check_beads_issue")
    def test_run_execution_fails_on_main(self, mock_beads, mock_branch):
        """Test execution fails if on main branch."""
        mock_branch.return_value = ("main", False)
        mock_beads.return_value = (True, "Issues ready: 1")

        with patch("builtins.print"):
            result = orchestrator.run_execution()
        self.assertFalse(result)


class TestOrchestratorFinalization(unittest.TestCase):
    """Test the run_finalization function."""

    @patch("check_protocol_compliance_mirror.run_phase_from_json")
    @patch("check_protocol_compliance_mirror.prune_local_branches")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.check_sop_simplification")
    @patch("check_protocol_compliance_mirror.check_handoff_compliance")
    @patch("check_protocol_compliance_mirror.validate_atomic_commits")
    @patch("check_protocol_compliance_mirror.check_reflection_invoked")
    @patch("check_protocol_compliance_mirror.check_linked_repositories")
    @patch("check_protocol_compliance_mirror.check_code_review_status")
    @patch("check_protocol_compliance_mirror.check_no_separate_review_issues")
    @patch("check_protocol_compliance_mirror.check_todo_completion")
    @patch("check_protocol_compliance_mirror.check_hook_integrity")
    @patch("check_protocol_compliance_mirror.check_pr_exists")
    @patch("check_protocol_compliance_mirror.check_pr_decomposition_closure")
    @patch("check_protocol_compliance_mirror.check_child_pr_linkage")
    @patch("check_protocol_compliance_mirror.check_handoff_pr_verification")
    @patch("check_protocol_compliance_mirror.check_beads_pr_sync")
    @patch("check_protocol_compliance_mirror.check_workspace_cleanup")
    def test_run_finalization_success(
        self,
        mock_cleanup,
        mock_sync,
        mock_verification,
        mock_linkage,
        mock_decomposition,
        mock_pr,
        mock_hook,
        mock_todo,
        mock_pr_review,
        mock_code_review,
        mock_linked,
        mock_reflect,
        mock_atomic,
        mock_handoff,
        mock_simplify,
        mock_branch,
        mock_git,
        mock_prune,
        mock_json_phase,
    ):
        """Test successful finalization."""
        mock_json_phase.return_value = (False, [], [])
        mock_prune.return_value = (True, "No stale branches")
        mock_git.return_value = (True, "Working directory clean")
        mock_branch.return_value = ("agent-harness/test", True)
        mock_simplify.return_value = (True, "No simplifications")
        mock_handoff.return_value = (True, "No handoffs")
        mock_atomic.return_value = (True, [])
        mock_reflect.return_value = (True, "Reflection captured")
        mock_linked.return_value = (True, [])
        mock_code_review.return_value = (True, "Code Review passed")
        mock_pr_review.return_value = (True, "PR review issue found")
        mock_todo.return_value = (True, "All tasks completed")
        mock_hook.return_value = (True, "Hooks intact")
        mock_pr.return_value = (True, "PR found")
        mock_decomposition.return_value = (True, "Protocol followed")
        mock_linkage.return_value = (True, "Linkage OK")
        mock_verification.return_value = (True, "Verification OK")
        mock_sync.return_value = (True, "Sync OK")
        mock_cleanup.return_value = (True, "Cleanup OK")

        with patch("builtins.print"):
            result = orchestrator.run_finalization()
        self.assertTrue(result)

    @patch("check_protocol_compliance_mirror.check_git_status")
    def test_run_finalization_blocked_by_git(self, mock_git):
        """Test finalization blocked by uncommitted changes."""
        mock_git.return_value = (False, "Uncommitted changes: M file.py")

        with patch("builtins.print"):
            result = orchestrator.run_finalization()
        self.assertFalse(result)

    @patch("check_protocol_compliance_mirror.run_phase_from_json")
    @patch("check_protocol_compliance_mirror.prune_local_branches")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.check_sop_simplification")
    @patch("check_protocol_compliance_mirror.check_handoff_compliance")
    @patch("check_protocol_compliance_mirror.validate_atomic_commits")
    @patch("check_protocol_compliance_mirror.check_reflection_invoked")
    @patch("check_protocol_compliance_mirror.check_linked_repositories")
    @patch("check_protocol_compliance_mirror.check_code_review_status")
    @patch("check_protocol_compliance_mirror.check_no_separate_review_issues")
    @patch("check_protocol_compliance_mirror.check_todo_completion")
    @patch("check_protocol_compliance_mirror.check_hook_integrity")
    @patch("check_protocol_compliance_mirror.check_pr_exists")
    @patch("check_protocol_compliance_mirror.check_pr_decomposition_closure")
    @patch("check_protocol_compliance_mirror.check_child_pr_linkage")
    @patch("check_protocol_compliance_mirror.check_handoff_pr_verification")
    @patch("check_protocol_compliance_mirror.check_beads_pr_sync")
    @patch("check_protocol_compliance_mirror.check_workspace_cleanup")
    def test_run_finalization_blocked_by_stale_branches(
        self,
        mock_cleanup,
        mock_sync,
        mock_verification,
        mock_linkage,
        mock_decomposition,
        mock_pr,
        mock_hook,
        mock_todo,
        mock_pr_review,
        mock_code_review,
        mock_linked,
        mock_reflect,
        mock_atomic,
        mock_handoff,
        mock_simplify,
        mock_branch,
        mock_git,
        mock_prune,
        mock_json_phase,
    ):
        """Test finalization blocked by stale branches."""
        mock_json_phase.return_value = (False, [], [])
        mock_git.return_value = (True, "Working directory clean")
        mock_branch.return_value = ("feature/test", True)
        mock_simplify.return_value = (True, "No simplifications")
        mock_handoff.return_value = (True, "No handoffs")
        mock_atomic.return_value = (True, [])
        mock_reflect.return_value = (True, "Reflection captured")
        mock_linked.return_value = (True, [])
        mock_code_review.return_value = (True, "Code Review passed")
        mock_pr_review.return_value = (True, "PR review issue found")
        mock_todo.return_value = (True, "All tasks completed")
        mock_hook.return_value = (True, "Hooks intact")
        mock_pr.return_value = (True, "PR found")
        mock_decomposition.return_value = (True, "Protocol followed")
        mock_linkage.return_value = (True, "Linkage OK")
        mock_verification.return_value = (True, "Verification OK")
        mock_sync.return_value = (True, "Sync OK")
        mock_cleanup.return_value = (True, "Cleanup OK")

        # Simulating stale branches
        mock_prune.return_value = (False, "Stale branches detected: agent/old-feature")

        with patch("builtins.print"):
            result = orchestrator.run_finalization()
        self.assertFalse(result)

    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.check_reflection_invoked")
    def test_run_finalization_blocked_by_reflection(self, mock_reflect, mock_git):
        """Test finalization blocked by missing reflection."""
        mock_git.return_value = (True, "Working directory clean")
        mock_reflect.return_value = (False, "Reflection not captured")

        with patch("builtins.print"):
            result = orchestrator.run_finalization()
        self.assertFalse(result)


class TestOrchestratorRetrospective(unittest.TestCase):
    """Test the run_retrospective function."""

    @patch("check_protocol_compliance_mirror.run_phase_from_json")
    @patch("check_protocol_compliance_mirror.check_reflection_invoked")
    @patch("check_protocol_compliance_mirror.check_debriefing_invoked")
    @patch("check_protocol_compliance_mirror.check_plan_approval")
    @patch("check_protocol_compliance_mirror.check_progress_log_exists")
    @patch("check_protocol_compliance_mirror.check_todo_completion")
    @patch("check_protocol_compliance_mirror.check_handoff_pr_link")
    @patch("check_protocol_compliance_mirror.check_handoff_beads_id")
    @patch("check_protocol_compliance_mirror.check_wrapup_indicator_symmetry")
    @patch("check_protocol_compliance_mirror.check_wrapup_exclusivity")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.inject_debrief_to_beads")
    def test_run_retrospective_success(
        self,
        mock_inject,
        mock_git,
        mock_exclusivity,
        mock_symmetry,
        mock_handoff_id,
        mock_handoff_pr,
        mock_todo,
        mock_log,
        mock_approval,
        mock_debrief,
        mock_reflect,
        mock_json_phase,
    ):
        """Test successful retrospective."""
        mock_reflect.return_value = (True, "Reflection captured")
        mock_inject.return_value = (True, "Injected")
        mock_debrief.return_value = (True, "Debrief generated")
        mock_approval.return_value = (False, "Plan approval is stale")  # Stale means cleared
        mock_log.return_value = (True, "Log exists")
        mock_todo.return_value = (True, "Tasks complete")
        mock_handoff_pr.return_value = (True, "PR link found")
        mock_handoff_id.return_value = (True, "ID found")
        mock_symmetry.return_value = (True, "Symmetry OK")
        mock_exclusivity.return_value = (True, "Exclusivity OK")

        # Mock reflector synthesis in log
        with patch("check_protocol_compliance_mirror.Path.home") as mock_home:
            mock_log_file = MagicMock()
            mock_log_file.read_text.return_value = "## Reflector Synthesis\nSome content"
            # Path.home() / ".agent/progress-logs" / "test-id.md"
            # 1. Path.home() / ".agent/progress-logs" -> returns h1
            # 2. h1 / "test-id.md" -> returns mock_log_file
            mock_home.return_value.__truediv__.return_value.__truediv__.return_value = mock_log_file

            # Mock get_active_issue_id to ensure it matches the path we mocked
            with patch("check_protocol_compliance_mirror.get_active_issue_id") as mock_id:
                mock_id.return_value = "test-id"
                mock_git.return_value = (True, "Clean")
                mock_json_phase.return_value = (False, [], [])
                with patch("builtins.print"):
                    result = orchestrator.run_retrospective()
        self.assertTrue(result)


class TestOrchestratorCleanState(unittest.TestCase):
    """Test the run_clean_state function."""

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.check_git_status")
    @patch("check_protocol_compliance_mirror.Path")
    @patch("subprocess.run")
    @patch("check_protocol_compliance_mirror.prune_local_branches")
    @patch("check_protocol_compliance_mirror.check_workspace_cleanup")
    def test_run_clean_state_success(
        self, mock_cleanup, mock_prune, mock_run, mock_path, mock_git, mock_branch
    ):
        """Test successful clean state check."""
        mock_branch.return_value = ("main", False)  # On main, not feature
        mock_git.return_value = (True, "Clean")
        mock_run.return_value.stdout = "Your branch is up to date"
        mock_path.return_value.glob.return_value = []
        mock_prune.return_value = (True, "Branches pruned")
        mock_cleanup.return_value = (True, "Cleanup OK")

        with patch("builtins.print"):
            result = orchestrator.run_clean_state()
        self.assertTrue(result)

    def test_run_clean_state_fails_on_feature_branch(self):
        """Test clean state fails if still on feature branch."""
        with patch("check_protocol_compliance_mirror.check_branch_info") as mock_branch:
            mock_branch.return_value = ("agent-harness/test", True)
            with patch("check_protocol_compliance_mirror.check_git_status") as mock_git:
                mock_git.return_value = (True, "Clean")
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.stdout = "Up to date"
                    with patch("builtins.print"):
                        result = orchestrator.run_clean_state()
        self.assertFalse(result)


class TestOrchestratorPRReview(unittest.TestCase):
    """Test the PR review issue validation function."""

    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.check_branch_info")
    @patch("validators.finalization_validator.subprocess.run")
    def test_check_pr_review_issue_exists(self, mock_run, mock_branch, mock_tool, mock_id):
        """Test PR review issue found when P0 issue with 'PR Review' exists."""
        mock_tool.return_value = True
        mock_branch.return_value = ("agent-harness/test-branch", True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "abc-123: PR Review: test-branch"
        mock_run.return_value = mock_result
        mock_id.return_value = "abc-123"

        passed, msg = orchestrator.check_no_separate_review_issues()
        self.assertTrue(passed)
        self.assertIn("No separate PR review issues detected", msg)

    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.check_branch_info")
    @patch("validators.finalization_validator.subprocess.run")
    def test_check_pr_review_issue_missing(self, mock_run, mock_branch, mock_tool, mock_id):
        """Test failure when no P0 PR review issue exists."""
        mock_tool.return_value = True
        mock_branch.return_value = ("agent-harness/new-feature", True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""  # No issues
        mock_run.return_value = mock_result
        mock_id.return_value = "new-feature"

        passed, msg = orchestrator.check_no_separate_review_issues()
        self.assertTrue(passed)
        self.assertIn("No open issues found", msg)

    @patch("validators.finalization_validator.check_branch_info")
    @patch("validators.finalization_validator.check_tool_available")
    def test_check_pr_review_not_needed_on_main(self, mock_tool, mock_branch):
        """Test PR review not required when on main branch."""
        mock_tool.return_value = True
        mock_branch.return_value = ("main", False)

        passed, msg = orchestrator.check_no_separate_review_issues()
        self.assertTrue(passed)
        self.assertIn("Not on feature branch", msg)

    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.subprocess.run")
    @patch("validators.finalization_validator.check_branch_info")
    def test_check_pr_review_issue_branch_match(self, mock_branch, mock_run, mock_tool, mock_id):
        """Test PR review issue found by branch name match."""
        mock_tool.return_value = True
        mock_branch.return_value = ("agent-harness/agent-harness-xyz", True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "xyz-456: Some issue mentioning agent-harness-xyz"
        mock_run.return_value = mock_result
        mock_id.return_value = "xyz-456"

        passed, msg = orchestrator.check_no_separate_review_issues()
        self.assertTrue(passed)
        self.assertIn("No separate PR review issues detected", msg)


class TestOrchestratorPRChecks(unittest.TestCase):
    """Test the PR existance and handoff link checks."""

    @patch("validators.finalization_validator.check_branch_info")
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.subprocess.run")
    def test_check_pr_exists_success(self, mock_run, mock_tool, mock_branch):
        """Test PR exists search success."""
        mock_tool.return_value = True
        mock_branch.return_value = ("agent-harness/test", True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/owner/repo/pull/1"
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_pr_exists()
        self.assertTrue(passed)
        self.assertIn("PR found", msg)

    @patch("validators.finalization_validator.check_branch_info")
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.subprocess.run")
    def test_check_pr_exists_missing(self, mock_run, mock_tool, mock_branch):
        """Test PR missing detection."""
        mock_tool.return_value = True
        mock_branch.return_value = ("agent-harness/test", True)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_pr_exists()
        self.assertFalse(passed)
        self.assertIn("No PR found", msg)

    @patch("check_protocol_compliance_mirror.Path.home")
    def test_check_handoff_pr_link_success(self, mock_home):
        """Test PR link found in debrief."""
        mock_session = MagicMock()
        mock_session.is_dir.return_value = True
        mock_session.stat.return_value.st_mtime = 123456789

        mock_brain_dir = MagicMock()
        mock_brain_dir.exists.return_value = True
        mock_brain_dir.iterdir.return_value = [mock_session]

        mock_debrief = MagicMock()
        mock_debrief.exists.return_value = True
        mock_debrief.read_text.return_value = (
            "Work complete. PR Link: https://github.com/owner/repo/pull/1"
        )
        mock_debrief.name = "debrief.md"

        # mock_home() / ".gemini" / "antigravity" / "brain"
        mock_h1 = MagicMock()
        mock_h2 = MagicMock()
        mock_home.return_value.__truediv__.return_value = mock_h1
        mock_h1.__truediv__.return_value = mock_h2
        mock_h2.__truediv__.return_value = mock_brain_dir

        # session_dir / "debrief.md"
        mock_session.__truediv__.return_value = mock_debrief

        passed, msg = orchestrator.check_handoff_pr_link()
        self.assertTrue(passed)
        self.assertIn("PR link found", msg)


if __name__ == "__main__":
    unittest.main()
