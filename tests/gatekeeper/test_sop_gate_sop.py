"""
Test suite for Beads Issue Requirement SOP gate enforcement.
# Gate: docs/sop/SOP.md (Lines: 13, 149)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the Orchestrator script path
orchestrator_path = Path.home() / ".gemini/antigravity/skills/Orchestrator/scripts"
sys.path.insert(0, str(orchestrator_path))

try:
    import check_protocol_compliance as orchestrator
except ImportError:
    orchestrator = None


class TestGateBeadsIssue:
    """Tests for mandatory Beads issue presence."""

    @patch("check_protocol_compliance.check_tool_available")
    @patch("check_protocol_compliance.subprocess.run")
    def test_missing_issue_blocked(self, mock_run, mock_tool):
        """Verify that work is blocked if no Beads issue is active."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_tool.return_value = True
        # Mock bd ready returning no issues
        mock_run.return_value = MagicMock(returncode=1, stdout="")

        passed, msg = orchestrator.check_beads_issue()
        assert passed is False
        assert "No active Beads issues" in msg

    @patch("check_protocol_compliance.check_tool_available")
    @patch("check_protocol_compliance.subprocess.run")
    def test_active_issue_passes(self, mock_run, mock_tool):
        """Verify that work passes if a Beads issue is active."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_tool.return_value = True
        # Mock bd ready returning one issue
        mock_run.return_value = MagicMock(returncode=0, stdout="agent-harness-123: Test issue")

        passed, msg = orchestrator.check_beads_issue()
        assert passed is True
        assert "Issues ready: 1" in msg
