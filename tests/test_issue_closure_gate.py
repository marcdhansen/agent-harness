import unittest
from unittest.mock import MagicMock, patch

from agent_harness.compliance import check_issue_closure_gate


class TestIssueClosureGate(unittest.TestCase):
    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.subprocess.run")
    def test_gate_pass_in_review(self, mock_run, mock_id, mock_tool):
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"

        # Mock bd output for issue status
        # Note: In compliance.py, we might use "bd show <id> --json" which returns a list or object depending on implementation.
        # Assuming list:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"id": "issue-123", "status": "in_review"}]'

        mock_run.return_value = mock_result

        passed, msg = check_issue_closure_gate()
        self.assertTrue(passed)
        self.assertIn("Issue issue-123 has acceptable status", msg)

    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.subprocess.run")
    def test_gate_fail_open(self, mock_run, mock_id, mock_tool):
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"id": "issue-123", "status": "open"}]'
        mock_run.return_value = mock_result

        passed, msg = check_issue_closure_gate()
        self.assertFalse(passed)
        self.assertIn("has status 'open'", msg)

    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.subprocess.run")
    def test_gate_fail_started(self, mock_run, mock_id, mock_tool):
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"id": "issue-123", "status": "started"}]'
        mock_run.return_value = mock_result

        passed, msg = check_issue_closure_gate()
        self.assertFalse(passed)
        self.assertIn("has status 'started'", msg)

    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.subprocess.run")
    def test_gate_pass_closed(self, mock_run, mock_id, mock_tool):
        mock_tool.return_value = True
        mock_id.return_value = "issue-123"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '[{"id": "issue-123", "status": "closed"}]'
        mock_run.return_value = mock_result

        passed, msg = check_issue_closure_gate()
        self.assertTrue(passed)
        self.assertIn("Issue issue-123 has acceptable status", msg)


if __name__ == "__main__":
    unittest.main()
