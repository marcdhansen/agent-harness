import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add orchestrator script path
orchestrator_path = Path(__file__).parent / "orchestrator_mirror"
sys.path.insert(0, str(orchestrator_path))

from validators.git_validator import check_branch_issue_coupling  # noqa: E402


class TestBranchIssueCouplingHardening(unittest.TestCase):
    @patch("validators.git_validator.check_branch_info")
    def test_coupling_fails_on_random_branch(self, mock_branch_info):
        """Test that coupling fails on a branch that doesn't follow convention."""
        mock_branch_info.return_value = ("my-patch", False)
        passed, msg = check_branch_issue_coupling()
        self.assertFalse(passed)
        self.assertIn("PROTOCOL VIOLATION", msg)

    @patch("validators.git_validator.check_branch_info")
    def test_coupling_passes_on_main(self, mock_branch_info):
        """Test that coupling passes (skipped) on main."""
        mock_branch_info.return_value = ("main", False)
        passed, msg = check_branch_issue_coupling()
        self.assertTrue(passed)
        self.assertIn("protected base branch", msg)

    @patch("validators.git_validator.check_branch_info")
    @patch("subprocess.run")
    def test_coupling_fails_on_unstarted_issue(self, mock_run, mock_branch_info):
        """Test that coupling fails if the issue is not in started state."""
        mock_branch_info.return_value = ("agent/task-123", True)

        # Mock 'bd show' output
        mock_show = MagicMock()
        mock_show.returncode = 0
        mock_show.stdout = json.dumps({"id": "task-123", "labels": ["status:open"]})
        mock_run.return_value = mock_show

        passed, msg = check_branch_issue_coupling()
        self.assertFalse(passed)
        self.assertIn("NOT in 'started' state", msg)


if __name__ == "__main__":
    unittest.main()
