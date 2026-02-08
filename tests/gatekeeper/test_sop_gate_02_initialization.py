"""
Test suite for Plan Approval Freshness SOP gate enforcement.
# Gate: docs/phases/02_initialization.md (Lines: 3, 103)
"""
import pytest
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the Orchestrator script path
orchestrator_path = Path.home() / ".gemini/antigravity/skills/Orchestrator/scripts"
sys.path.insert(0, str(orchestrator_path))

try:
    import check_protocol_compliance as orchestrator
except ImportError:
    orchestrator = None

class TestGatePlanApproval:
    """Tests for recent plan approval."""

    @patch("check_protocol_compliance.Path.exists")
    def test_missing_approval_blocked(self, mock_exists):
        """Verify that missing plan approval is blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = False
        passed, msg = orchestrator.check_plan_approval()
        assert passed is False
        assert "No plan approval found" in msg

    @patch("check_protocol_compliance.Path.exists")
    @patch("check_protocol_compliance.Path.read_text")
    @patch("check_protocol_compliance.Path.stat")
    @patch("check_protocol_compliance.Path.iterdir")
    def test_stale_approval_blocked(self, mock_iterdir, mock_stat, mock_read, mock_exists):
        """Verify that stale plan approval (>4 hours) is blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = True
        mock_read.return_value = "## Approval\n[x] Approved"
        
        # Mock brain dir iteration
        mock_session_dir = MagicMock(spec=Path)
        mock_session_dir.is_dir.return_value = True
        mock_session_dir.__truediv__.return_value = mock_session_dir
        mock_session_dir.exists.return_value = True
        mock_session_dir.read_text.return_value = "## Approval\n[x] Approved"
        
        mock_iterdir.return_value = [mock_session_dir]

        # Mock stat for the task.md file
        mock_st = MagicMock()
        mock_st.st_mtime = time.time() - (5 * 3600)
        mock_st.st_mode = 33188 # Regular file
        mock_stat.return_value = mock_st

        passed, msg = orchestrator.check_plan_approval()
        assert passed is False
        assert "stale" in msg.lower()

    @patch("check_protocol_compliance.Path.exists")
    @patch("check_protocol_compliance.Path.read_text")
    @patch("check_protocol_compliance.Path.stat")
    @patch("check_protocol_compliance.Path.iterdir")
    def test_recent_approval_passes(self, mock_iterdir, mock_stat, mock_read, mock_exists):
        """Verify that recent plan approval (<4 hours) passes."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = True
        mock_read.return_value = "## Approval\n[x] Approved"
        
        # Mock brain dir iteration
        mock_session_dir = MagicMock(spec=Path)
        mock_session_dir.is_dir.return_value = True
        mock_session_dir.__truediv__.return_value = mock_session_dir
        mock_session_dir.exists.return_value = True
        mock_session_dir.read_text.return_value = "## Approval\n[x] Approved"
        
        mock_iterdir.return_value = [mock_session_dir]

        # Mock stat for the task.md file
        mock_st = MagicMock()
        mock_st.st_mtime = time.time() - 1800
        mock_st.st_mode = 33188 # Regular file
        mock_stat.return_value = mock_st

        passed, msg = orchestrator.check_plan_approval()
        assert passed is True
        assert "Plan approved" in msg
