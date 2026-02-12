import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
from agent_harness.compliance import (
    check_handoff_pr_verification,
    check_beads_pr_sync,
    check_pr_review_issue_created,
    check_pr_exists,
    check_pr_decomposition_closure,
    check_child_pr_linkage,
    check_workspace_cleanup,
    get_active_issue_id
)

class TestPortedValidators(unittest.TestCase):
    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.check_branch_info")
    def test_handoff_pr_verification_success(self, mock_branch, mock_run, mock_id, mock_tool):
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"
        mock_branch.return_value = ("agent/issue-123", True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {
                "number": 1,
                "title": "[issue-123] Test PR",
                "headRefName": "agent/issue-123",
                "url": "https://github.com/PR1"
            }
        ])
        mock_run.return_value = mock_result

        passed, msg = check_handoff_pr_verification()
        self.assertTrue(passed)
        self.assertIn("Handoff PR verified", msg)

    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.check_branch_info")
    def test_beads_pr_sync_success(self, mock_branch, mock_run, mock_id, mock_tool):
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"
        mock_branch.return_value = ("agent/issue-123", True)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "title": "[issue-123] Implementation",
            "body": "Fixes issue-123"
        })
        mock_run.return_value = mock_result

        passed, msg = check_beads_pr_sync()
        self.assertTrue(passed)
        self.assertIn("properly synchronized", msg)

    @patch("agent_harness.compliance.subprocess.run")
    def test_workspace_cleanup_clean(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "task.md\ndebrief.md\n.reflection_input.json"
        mock_run.return_value = mock_result

        passed, msg = check_workspace_cleanup()
        self.assertTrue(passed)
        self.assertIn("clean of temporary artifact drift", msg)

    @patch("agent_harness.compliance.subprocess.run")
    def test_workspace_cleanup_drift(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "task.md\njunk.bak"
        mock_run.return_value = mock_result

        passed, msg = check_workspace_cleanup()
        self.assertFalse(passed)
        self.assertIn("Suspicious temporary files detected", msg)

    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.check_branch_info")
    @patch("agent_harness.compliance.subprocess.run")
    def test_pr_exists_success(self, mock_run, mock_branch, mock_tool):
        mock_tool.return_value = True
        mock_branch.return_value = ("agent/issue-123", True)
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/pull/1"
        mock_run.return_value = mock_result

        passed, msg = check_pr_exists()
        self.assertTrue(passed)
        self.assertIn("PR found", msg)

if __name__ == "__main__":
    unittest.main()
