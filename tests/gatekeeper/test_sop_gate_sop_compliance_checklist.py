"""
Test suite for Reflection Capture SOP gate enforcement.
# Gate: docs/SOP_COMPLIANCE_CHECKLIST.md (Lines: 101, 103)
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

class TestGateReflection:
    """Tests for recent reflection capture."""

    @patch("pathlib.Path.exists")
    def test_missing_reflection_blocked(self, mock_exists):
        """Verify that missing reflection is blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = False
        passed, msg = orchestrator.check_reflection_invoked()
        assert passed is False
        assert "No recent reflection" in msg

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_stale_reflection_blocked(self, mock_stat, mock_exists):
        """Verify that stale reflection (>2 hours) is blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = True
        # Mock mtime to be 3 hours ago
        mock_st = MagicMock()
        mock_st.st_mtime = time.time() - (3 * 3600)
        mock_stat.return_value = mock_st

        passed, msg = orchestrator.check_reflection_invoked()
        assert passed is False
        assert "No recent reflection" in msg

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_recent_reflection_passes(self, mock_stat, mock_exists):
        """Verify that recent reflection (<2 hours) passes."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = True
        # Mock mtime to be 10 minutes ago
        mock_st = MagicMock()
        mock_st.st_mtime = time.time() - 600
        mock_stat.return_value = mock_st

        passed, msg = orchestrator.check_reflection_invoked()
        assert passed is True
        assert "Reflection captured" in msg
