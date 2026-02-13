import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from agent_harness.compliance import inject_debrief_to_beads

class TestDebriefInjection(unittest.TestCase):
    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.Path.home")
    def test_debrief_injection_success(self, mock_home, mock_get_id, mock_run):
        """Test successful injection of debrief.md into Beads."""
        mock_get_id.return_value = "agent-harness-gf6"
        
        # Setup mock brain directory
        temp_dir = MagicMock(spec=Path)
        mock_home.return_value = temp_dir
        
        brain_dir = temp_dir / ".gemini" / "antigravity" / "brain"
        brain_dir.exists.return_value = True
        
        session_dir = MagicMock(spec=Path)
        session_dir.is_dir.return_value = True
        session_dir.stat().st_mtime = 1000
        
        brain_dir.iterdir.return_value = [session_dir]
        
        debrief_file = session_dir / "debrief.md"
        debrief_file.exists.return_value = True
        debrief_file.read_text.return_value = "## Implementation Details\nDone stuff."
        
        # Mock bd show to NOT contain the implementation details (not injected yet)
        mock_show_res = MagicMock()
        mock_show_res.returncode = 0
        mock_show_res.stdout = "Issue details..."
        
        # Mock bd comments add
        mock_add_res = MagicMock()
        mock_add_res.returncode = 0
        
        mock_run.side_effect = [mock_show_res, mock_add_res]
        
        passed, msg = inject_debrief_to_beads()
        self.assertTrue(passed)
        self.assertIn("Injected debrief", msg)
        
    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.get_active_issue_id")
    @patch("agent_harness.compliance.Path.home")
    def test_debrief_injection_already_exists(self, mock_home, mock_get_id, mock_run):
        """Test that injection is skipped if content already exists in comments."""
        mock_get_id.return_value = "agent-harness-gf6"
        
        # Setup mock brain directory
        temp_dir = MagicMock(spec=Path)
        mock_home.return_value = temp_dir
        
        brain_dir = temp_dir / ".gemini" / "antigravity" / "brain"
        brain_dir.exists.return_value = True
        
        session_dir = MagicMock(spec=Path)
        session_dir.is_dir.return_value = True
        session_dir.stat().st_mtime = 1000
        
        brain_dir.iterdir.return_value = [session_dir]
        
        debrief_file = session_dir / "debrief.md"
        debrief_file.exists.return_value = True
        debrief_file.read_text.return_value = "## Implementation Details\nDone stuff."
        
        # Mock bd show to CONTAIN the implementation details
        mock_show_res = MagicMock()
        mock_show_res.returncode = 0
        mock_show_res.stdout = "Done stuff."
        
        mock_run.return_value = mock_show_res
        
        passed, msg = inject_debrief_to_beads()
        self.assertTrue(passed)
        self.assertIn("already exists", msg)

if __name__ == "__main__":
    unittest.main()
