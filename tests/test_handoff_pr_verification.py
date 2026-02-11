import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import sys
import os

# Add the orchestrator script path to sys.path
orchestrator_path = Path.home() / ".gemini/antigravity/skills/Orchestrator/scripts"
sys.path.append(str(orchestrator_path))

try:
    from validators.finalization_validator import check_handoff_pr_verification
except ImportError:
    # Handle environment where validators might not be directly importable
    # (e.g. if running from a different root)
    pass


class TestHandoffPRVerification(unittest.TestCase):
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.subprocess.run")
    @patch("validators.finalization_validator.check_branch_info")
    def test_handoff_success(self, mock_branch, mock_run, mock_id, mock_tool):
        """Test success when matching PR is found."""
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"
        mock_branch.return_value = ("agent/issue-123", True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            [
                {
                    "number": 1,
                    "title": "[issue-123] Test PR",
                    "headRefName": "agent/issue-123",
                    "url": "https://github.com/PR1",
                }
            ]
        )
        mock_run.return_value = mock_result

        passed, msg = check_handoff_pr_verification()
        self.assertTrue(passed)
        self.assertIn("Handoff PR verified", msg)

    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.subprocess.run")
    def test_handoff_multiple_prs(self, mock_run, mock_id, mock_tool):
        """Test failure when multiple PRs are found for the same issue."""
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            [
                {
                    "number": 1,
                    "title": "[issue-123] PR 1",
                    "headRefName": "branch-1",
                    "url": "https://github.com/PR1",
                },
                {
                    "number": 2,
                    "title": "[issue-123] PR 2",
                    "headRefName": "branch-2",
                    "url": "https://github.com/PR2",
                },
            ]
        )
        mock_run.return_value = mock_result

        passed, msg = check_handoff_pr_verification()
        self.assertFalse(passed)
        self.assertIn("Multiple open PRs found", msg)

    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.subprocess.run")
    @patch("validators.finalization_validator.check_branch_info")
    def test_handoff_branch_mismatch(self, mock_branch, mock_run, mock_id, mock_tool):
        """Test failure when PR branch doesn't match current branch."""
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"
        mock_branch.return_value = ("agent/issue-123-NEW", True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            [
                {
                    "number": 1,
                    "title": "[issue-123] Test PR",
                    "headRefName": "agent/issue-123-OLD",
                    "url": "https://github.com/PR1",
                }
            ]
        )
        mock_run.return_value = mock_result

        passed, msg = check_handoff_pr_verification()
        self.assertFalse(passed)
        self.assertIn("suggests workspace drift", msg)

    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.subprocess.run")
    def test_handoff_no_prs(self, mock_run, mock_id, mock_tool):
        """Test success when no PRs are found (not a violation, usually handled by other checks)."""
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        mock_run.return_value = mock_result

        passed, msg = check_handoff_pr_verification()
        self.assertTrue(passed)
        self.assertIn("No open PRs found", msg)


class TestBeadsPRSync(unittest.TestCase):
    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.subprocess.run")
    @patch("validators.finalization_validator.check_branch_info")
    def test_sync_success_title(self, mock_branch, mock_run, mock_id, mock_tool):
        """Test success when issue ID is in PR title."""
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"
        mock_branch.return_value = ("feature/test", True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(
            {"title": "[issue-123] Feature Implementation", "body": "Some description"}
        )
        mock_run.return_value = mock_result

        from validators.finalization_validator import check_beads_pr_sync

        passed, msg = check_beads_pr_sync()
        self.assertTrue(passed)
        self.assertIn("properly synchronized", msg)

    @patch("validators.finalization_validator.check_tool_available")
    @patch("validators.finalization_validator.get_active_issue_id")
    @patch("validators.finalization_validator.subprocess.run")
    @patch("validators.finalization_validator.check_branch_info")
    def test_sync_failure(self, mock_branch, mock_run, mock_id, mock_tool):
        """Test failure when issue ID is missing from PR."""
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"
        mock_branch.return_value = ("feature/test", True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"title": "Fix some bug", "body": "No reference here"})
        mock_run.return_value = mock_result

        from validators.finalization_validator import check_beads_pr_sync

        passed, msg = check_beads_pr_sync()
        self.assertFalse(passed)
        self.assertIn("PROTOCOL VIOLATION", msg)


class TestWorkspaceCleanup(unittest.TestCase):
    @patch("validators.finalization_validator.subprocess.run")
    def test_cleanup_clean(self, mock_run):
        """Test success when no drift is detected."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "task.md\ndebrief.md"
        mock_run.return_value = mock_result

        from validators.finalization_validator import check_workspace_cleanup

        passed, msg = check_workspace_cleanup()
        self.assertTrue(passed)
        self.assertIn("clean of temporary artifact drift", msg)

    @patch("validators.finalization_validator.subprocess.run")
    def test_cleanup_suspicious(self, mock_run):
        """Test failure when suspicious files are found."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "task.md.bak\njunk.tmp"
        mock_run.return_value = mock_result

        from validators.finalization_validator import check_workspace_cleanup

        passed, msg = check_workspace_cleanup()
        self.assertFalse(passed)
        self.assertIn("Suspicious temporary files detected", msg)


if __name__ == "__main__":
    unittest.main()
