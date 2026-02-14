import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from agent_harness.compliance import check_handoff_beads_id, check_protocol_compliance_reporting


class TestBeadsIDValidator(unittest.TestCase):
    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_beads_id_found(self, mock_home, mock_check_output):
        """Test success when Beads ID is found in debrief.md."""
        mock_check_output.return_value = "agent/agent-harness-123-fix\n"

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
        debrief_file.read_text.return_value = "This session handles agent-harness-123."

        passed, msg = check_handoff_beads_id()
        self.assertTrue(passed)
        self.assertIn("verified in", msg)
        self.assertIn("agent-harness-123", msg)

    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_beads_id_not_found(self, mock_home, mock_check_output):
        """Test failure when Beads ID is missing from debrief.md."""
        mock_check_output.return_value = "agent/agent-harness-123-fix\n"

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
        self.assertIn("not found in any debrief.md", msg)

    @patch("agent_harness.compliance.subprocess.run")
    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_fallback_to_bd_list(self, mock_home, mock_check_output, mock_run):
        """Test fallback to bd list when branch doesn't provide ID."""
        mock_check_output.return_value = "main\n"  # Branch doesn't match agent/*

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "agent-harness-999: Some task"
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

    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_checks_multiple_sessions(self, mock_home, mock_check_output):
        """Test that multiple recent sessions are checked."""
        mock_check_output.return_value = "agent/agent-harness-123-fix\n"

        # Setup mock brain directory
        temp_dir = MagicMock(spec=Path)
        mock_home.return_value = temp_dir

        brain_dir = temp_dir / ".gemini" / "antigravity" / "brain"
        brain_dir.exists.return_value = True

        # Latest session (no ID)
        latest_session = MagicMock(spec=Path)
        latest_session.is_dir.return_value = True
        latest_session.stat().st_mtime = 2000
        latest_debrief = latest_session / "debrief.md"
        latest_debrief.exists.return_value = True
        latest_debrief.read_text.return_value = "No ID here."

        # Older session (has ID)
        older_session = MagicMock(spec=Path)
        older_session.is_dir.return_value = True
        older_session.stat().st_mtime = 1000
        older_debrief = older_session / "debrief.md"
        older_debrief.exists.return_value = True
        older_debrief.read_text.return_value = "agent-harness-123 is here."

        # Return both sessions - the validator sorts them and takes [:3]
        brain_dir.iterdir.return_value = [older_session, latest_session]

        passed, msg = check_handoff_beads_id()

        # It should pass now because it checks up to top 3 sessions
        self.assertTrue(passed)
        self.assertIn("agent-harness-123", msg)


class TestProtocolComplianceReportingValidator(unittest.TestCase):
    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_compliance_reporting_success(self, mock_home, mock_check_output):
        """Test success when compliance statement with ID and 🏁 is found."""
        mock_check_output.return_value = "agent/agent-harness-123-fix\n"

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
        debrief_file.read_text.return_value = (
            "Protocol Compliance: 100% verified via Orchestrator (agent-harness-123) 🏁"
        )

        passed, msg = check_protocol_compliance_reporting()
        self.assertTrue(passed)
        self.assertIn("Full protocol compliance reporting found", msg)

    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_compliance_reporting_missing_id(self, mock_home, mock_check_output):
        """Test failure when compliance statement is present but missing ID."""
        mock_check_output.return_value = "agent/agent-harness-123-fix\n"

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
        # Missing ID and 🏁
        debrief_file.read_text.return_value = "Protocol Compliance: 100% verified via Orchestrator."

        passed, msg = check_protocol_compliance_reporting()
        self.assertFalse(passed)
        self.assertIn("missing issue ID 'agent-harness-123' or 🏁", msg)

    @patch("agent_harness.compliance.subprocess.check_output")
    @patch("agent_harness.compliance.Path.home")
    def test_compliance_reporting_missing_entirely(self, mock_home, mock_check_output):
        """Test failure when compliance statement is missing entirely."""
        mock_check_output.return_value = "agent/agent-harness-123-fix\n"

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
        debrief_file.read_text.return_value = "Some other text."

        passed, msg = check_protocol_compliance_reporting()
        self.assertFalse(passed)
        self.assertIn("Missing required compliance statement", msg)


if __name__ == "__main__":
    unittest.main()
