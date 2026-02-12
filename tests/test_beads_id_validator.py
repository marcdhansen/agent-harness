import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from agent_harness.compliance import check_handoff_beads_id

class TestBeadsIDValidator(unittest.TestCase):
    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_beads_id_found(self, mock_home, mock_check_output):
        """Test success when Beads ID is found in debrief.md."""
        mock_check_output.return_value = "agent/issue-123\n"
        
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
        debrief_file.read_text.return_value = "This session handles issue-123."
        
        passed, msg = check_handoff_beads_id()
        self.assertTrue(passed)
        self.assertIn("found in debrief.md", msg)

    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_beads_id_not_found(self, mock_home, mock_check_output):
        """Test failure when Beads ID is missing from debrief.md."""
        mock_check_output.return_value = "agent/issue-123\n"
        
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
        debrief_file.read_text.return_value = "No mentions here."
        
        passed, msg = check_handoff_beads_id()
        self.assertFalse(passed)
        self.assertIn("not found in debrief.md", msg)

    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.Path.home")
    def test_fallback_to_bd_list(self, mock_home, mock_run, mock_check_output):
        """Test fallback to bd list when branch doesn't provide ID."""
        mock_check_output.return_value = "main\n" # Branch doesn't match agent/*
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([{"id": "agent-harness-999"}])
        mock_run.return_value = mock_result

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
        debrief_file.read_text.return_value = "Working on agent-harness-999."
        
        passed, msg = check_handoff_beads_id()
        self.assertTrue(passed)
        self.assertIn("agent-harness-999", msg)

if __name__ == "__main__":
    unittest.main()
