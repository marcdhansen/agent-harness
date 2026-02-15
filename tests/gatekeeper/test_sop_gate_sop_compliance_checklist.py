"""
Test suite for Reflection Capture SOP gate enforcement.
# Gate: docs/SOP_COMPLIANCE_CHECKLIST.md (Lines: 101, 103)
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add the Orchestrator script path
orchestrator_path = Path(__file__).parents[2] / "tests/orchestrator_mirror"
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

    @patch("validators.finalization_validator.json.load")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_stale_reflection_blocked(self, mock_stat, mock_exists, mock_file, mock_json_load):
        """Verify that stale reflection (>2 hours) is blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = True
        mock_json_load.return_value = {
            "session_name": "test",
            "outcome": "stale-check",
            "technical_learnings": [],
            "refactoring_candidates": [],
        }

        # Mock mtime to be 3 hours ago
        mock_st = MagicMock()
        mock_st.st_mtime = time.time() - (3 * 3600)
        mock_stat.return_value = mock_st

        passed, msg = orchestrator.check_reflection_invoked()
        assert passed is False
        assert "No recent reflection" in msg

    @patch("validators.finalization_validator.json.load")
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    def test_recent_reflection_passes(self, mock_stat, mock_exists, mock_file, mock_json_load):
        """Verify that recent reflection (<2 hours) passes."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_exists.return_value = True
        mock_json_load.return_value = {
            "session_name": "test",
            "outcome": "recent-check",
            "technical_learnings": [],
            "refactoring_candidates": [],
        }

        # Mock mtime to be 10 minutes ago
        mock_st = MagicMock()
        mock_st.st_mtime = time.time() - 600
        mock_stat.return_value = mock_st

        passed, msg = orchestrator.check_reflection_invoked()
        assert passed is True
        assert "Reflection captured" in msg
