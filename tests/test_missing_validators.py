import unittest
from unittest.mock import MagicMock, patch

from agent_harness.compliance import check_closed_issue_branches, check_rebase_status


class TestMissingValidators(unittest.TestCase):
    @patch("pathlib.Path.exists")
    def test_check_rebase_status_clean(self, mock_exists):
        mock_exists.return_value = False
        passed, msg = check_rebase_status()
        self.assertTrue(passed)
        self.assertIn("No active rebase", msg)

    @patch("pathlib.Path.exists")
    def test_check_rebase_status_active(self, mock_exists):
        # We need to be careful with Path.exists mocking since it's used elsewhere
        # But for this unit test it's fine
        mock_exists.side_effect = lambda: True
        passed, msg = check_rebase_status()
        self.assertFalse(passed)
        self.assertIn("Active rebase or merge detected", msg)

    @patch("agent_harness.compliance.check_tool_available")
    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.json.loads")
    def test_check_closed_issue_branches_stale(self, mock_json, mock_run, mock_tool):
        mock_tool.return_value = True

        # Mock git branch output
        mock_git = MagicMock()
        mock_git.returncode = 0
        mock_git.stdout = "main\nfeat/agent-harness-abc\n"

        # Mock bd show output
        mock_bd = MagicMock()
        mock_bd.returncode = 0
        mock_bd.stdout = '{"status": "closed"}'

        mock_run.side_effect = [mock_git, mock_bd]
        mock_json.return_value = {"status": "closed"}

        passed, msg = check_closed_issue_branches()
        self.assertFalse(passed)
        self.assertIn("Stale branches detected", msg)
        self.assertIn("agent-harness-abc", msg)


if __name__ == "__main__":
    unittest.main()
