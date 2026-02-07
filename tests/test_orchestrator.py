"""Tests for the Orchestrator's compliance checking logic."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the orchestrator script path to sys.path
orchestrator_path = Path.home() / ".gemini/antigravity/skills/Orchestrator/scripts"
sys.path.append(str(orchestrator_path))

# Import the functions to test
try:
    import check_protocol_compliance as orchestrator
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
        mock_result.stdout = " M README.md\n M .agent/task.md"
        mock_run.return_value = mock_result

        passed, msg = orchestrator.check_git_status(turbo=True)
        self.assertTrue(passed)
        self.assertIn("Metadata changes only", msg)

    @patch("subprocess.run")
    def test_git_status_code_change_escalation(self, mock_run):
        """Test git status when code files are changed in Turbo mode."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = " M src/main.py\n M tests/test_core.py"
        mock_run.value = mock_result # Wait, I used mock_run.value instead of return_value in thoughts
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

    @patch("check_protocol_compliance.check_tool_available")
    @patch("check_protocol_compliance.check_git_status")
    def test_run_turbo_initialization_success(self, mock_git, mock_tool):
        """Test successful Turbo initialization."""
        mock_tool.return_value = True
        mock_git.return_value = (True, "Working directory clean")

        with patch("builtins.print"):
            result = orchestrator.run_turbo_initialization()
        self.assertTrue(result)

    @patch("check_protocol_compliance.check_tool_available")
    @patch("check_protocol_compliance.check_git_status")
    def test_run_turbo_initialization_blocked_by_code(self, mock_git, mock_tool):
        """Test Turbo initialization blocked by code changes."""
        mock_tool.return_value = True
        mock_git.return_value = (False, "ESCALATION REQUIRED: Code changes detected")

        with patch("builtins.print"):
            result = orchestrator.run_turbo_initialization()
        self.assertFalse(result)

class TestOrchestratorExecution(unittest.TestCase):
    """Test the run_execution function."""

    @patch("check_protocol_compliance.check_branch_info")
    @patch("check_protocol_compliance.check_beads_issue")
    @patch("check_protocol_compliance.check_git_status")
    @patch("check_protocol_compliance.Path")
    def test_run_execution_success(self, mock_path, mock_git, mock_beads, mock_branch):
        """Test successful execution phase validation."""
        mock_branch.return_value = ("feature/test", True)
        mock_beads.return_value = (True, "Issues ready: 1")
        mock_git.return_value = (False, "Work in progress") # IFO expects changes
        
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

    @patch("check_protocol_compliance.check_branch_info")
    @patch("check_protocol_compliance.check_beads_issue")
    def test_run_execution_fails_on_main(self, mock_beads, mock_branch):
        """Test execution fails if on main branch."""
        mock_branch.return_value = ("main", False)
        mock_beads.return_value = (True, "Issues ready: 1")
        
        with patch("builtins.print"):
            result = orchestrator.run_execution()
        self.assertFalse(result)

class TestOrchestratorFinalization(unittest.TestCase):
    """Test the run_finalization function."""

    @patch("check_protocol_compliance.check_git_status")
    @patch("check_protocol_compliance.check_reflection_invoked")
    @patch("check_protocol_compliance.check_todo_completion")
    def test_run_finalization_success(self, mock_todo, mock_reflect, mock_git):
        """Test successful finalization."""
        mock_git.return_value = (True, "Working directory clean")
        mock_reflect.return_value = (True, "Reflection captured")
        mock_todo.return_value = (True, "All tasks completed")
        
        with patch("check_protocol_compliance.check_branch_info") as mock_branch:
            mock_branch.return_value = ("feature/test", True)
            with patch("builtins.print"):
                result = orchestrator.run_finalization()
        self.assertTrue(result)

    @patch("check_protocol_compliance.check_git_status")
    def test_run_finalization_blocked_by_git(self, mock_git):
        """Test finalization blocked by uncommitted changes."""
        mock_git.return_value = (False, "Uncommitted changes: M file.py")
        
        with patch("builtins.print"):
            result = orchestrator.run_finalization()
        self.assertFalse(result)

    @patch("check_protocol_compliance.check_git_status")
    @patch("check_protocol_compliance.check_reflection_invoked")
    def test_run_finalization_blocked_by_reflection(self, mock_reflect, mock_git):
        """Test finalization blocked by missing reflection."""
        mock_git.return_value = (True, "Working directory clean")
        mock_reflect.return_value = (False, "Reflection not captured")
        
        with patch("builtins.print"):
            result = orchestrator.run_finalization()
        self.assertFalse(result)

class TestOrchestratorRetrospective(unittest.TestCase):
    """Test the run_retrospective function."""

    @patch("check_protocol_compliance.check_reflection_invoked")
    @patch("check_protocol_compliance.check_debriefing_invoked")
    @patch("check_protocol_compliance.check_plan_approval")
    @patch("check_protocol_compliance.check_progress_log_exists")
    @patch("check_protocol_compliance.check_todo_completion")
    def test_run_retrospective_success(self, mock_todo, mock_log, mock_approval, mock_debrief, mock_reflect):
        """Test successful retrospective."""
        mock_reflect.return_value = (True, "Reflection captured")
        mock_debrief.return_value = (True, "Debrief generated")
        mock_approval.return_value = (False, "Plan approval is stale") # Stale means cleared
        mock_log.return_value = (True, "Log exists")
        mock_todo.return_value = (True, "Tasks complete")
        
        # Mock reflector synthesis in log
        with patch("check_protocol_compliance.get_active_issue_id") as mock_id:
            mock_id.return_value = "test-id"
            with patch("check_protocol_compliance.Path.home") as mock_home:
                mock_log_file = MagicMock()
                mock_log_file.read_text.return_value = "## Reflector Synthesis\nSome content"
                mock_home.return_value.__truediv__.return_value.__truediv__.return_value = mock_log_file
                
                with patch("builtins.print"):
                    result = orchestrator.run_retrospective()
        self.assertTrue(result)

class TestOrchestratorCleanState(unittest.TestCase):
    """Test the run_clean_state function."""

    @patch("check_protocol_compliance.check_branch_info")
    @patch("check_protocol_compliance.check_git_status")
    @patch("subprocess.run")
    def test_run_clean_state_success(self, mock_run, mock_git, mock_branch):
        """Test successful clean state check."""
        mock_branch.return_value = ("main", False) # On main, not feature
        mock_git.return_value = (True, "Clean")
        mock_run.return_value.stdout = "Your branch is up to date"
        
        with patch("builtins.print"):
            result = orchestrator.run_clean_state()
        self.assertTrue(result)

    def test_run_clean_state_fails_on_feature_branch(self):
        """Test clean state fails if still on feature branch."""
        with patch("check_protocol_compliance.check_branch_info") as mock_branch:
            mock_branch.return_value = ("feature/test", True)
            with patch("check_protocol_compliance.check_git_status") as mock_git:
                mock_git.return_value = (True, "Clean")
                with patch("subprocess.run") as mock_run:
                    mock_run.return_value.stdout = "Up to date"
                    with patch("builtins.print"):
                        result = orchestrator.run_clean_state()
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
