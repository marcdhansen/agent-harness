import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os
import json

# Add orchestrator script path
orchestrator_path = Path.home() / ".gemini/antigravity/skills/Orchestrator/scripts"
sys.path.append(str(orchestrator_path))

from validators.git_validator import get_active_issue_id
from validators.plan_validator import check_beads_issue

class TestBranchIssueCouplingEnforcement(unittest.TestCase):
    @patch("validators.git_validator.check_branch_info")
    @patch("subprocess.run")
    def test_get_active_issue_id_no_fallback_on_untracked_branch(self, mock_run, mock_branch_info):
        """Test that get_active_issue_id does NOT fall back to 'bd ready' on generic branches."""
        # Scenario: on a branch that doesn't follow agent/issue-id and is not a protected base branch
        mock_branch_info.return_value = ("fix-bug", False)
        
        # Mock 'bd ready' output (should not be called for fix-bug now)
        mock_ready = MagicMock()
        mock_ready.returncode = 0
        mock_ready.stdout = "1. [● P0] [task] task-abc: Title"
        mock_run.return_value = mock_ready
        
        issue_id = get_active_issue_id()
        # NEW BEHAVIOR: returns None for generic branches
        self.assertIsNone(issue_id)

    @patch("validators.git_validator.check_branch_info")
    @patch("subprocess.run")
    def test_get_active_issue_id_fallback_on_main(self, mock_run, mock_branch_info):
        """Test that get_active_issue_id still falls back to 'bd ready' on 'main'."""
        mock_branch_info.return_value = ("main", False)
        
        mock_ready = MagicMock()
        mock_ready.returncode = 0
        mock_ready.stdout = "1. [● P0] [task] task-abc: Title"
        mock_run.return_value = mock_ready
        
        issue_id = get_active_issue_id()
        self.assertEqual(issue_id, "task-abc")

    @patch("validators.git_validator.check_branch_info")
    @patch("subprocess.run")
    def test_get_active_issue_id_strict_on_feature_branch(self, mock_run, mock_branch_info):
        """Test that get_active_issue_id is strict on feature branches."""
        mock_branch_info.return_value = ("agent/task-123", True)
        
        issue_id = get_active_issue_id()
        self.assertEqual(issue_id, "task-123")
        # Should not have called subprocess.run for 'bd ready'
        self.assertEqual(mock_run.call_count, 0)

if __name__ == "__main__":
    unittest.main()
