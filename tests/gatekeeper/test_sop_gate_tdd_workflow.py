"""
Test suite for TDD Initialization Validation SOP gate enforcement.
# Gate: docs/sop/tdd-workflow.md (Lines: 14, 23)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the Orchestrator script path
orchestrator_path = Path(__file__).parents[2] / "tests/orchestrator_mirror"
sys.path.insert(0, str(orchestrator_path))

try:
    import check_protocol_compliance_mirror as orchestrator
except ImportError:
    orchestrator = None


class TestGateTDDPresence:
    """Tests for mandatory TDD presence before implementation."""

    @patch("check_protocol_compliance_mirror.check_tool_available")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_code_without_tests_blocked(self, mock_run, mock_tool):
        """Verify that code changes without corresponding test changes are blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        # Mock git status showing a new python file but no test file
        mock_tool.return_value = True
        mock_status = MagicMock()
        mock_status.returncode = 0
        mock_status.stdout = "A  src/new_feature.py\nM  README.md"

        def run_side_effect(cmd, **kwargs):
            if cmd[1] == "status":
                return mock_status
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        # Call the validation function (we assume we'll add this to check_protocol_compliance)
        if hasattr(orchestrator, "validate_tdd_compliance"):
            passed, msg = orchestrator.validate_tdd_compliance()
            assert passed is False
            assert "TDD Violation" in msg
            assert "src/new_feature.py" in msg
        else:
            # If function doesn't exist, the test should fail to prompt implementation (Red Phase)
            pytest.fail("validate_tdd_compliance function missing in Orchestrator")

    @patch("check_protocol_compliance_mirror.check_tool_available")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_tests_without_code_passes(self, mock_run, mock_tool):
        """Verify that test stubs without implementation code pass (Red Phase)."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        # Mock git status showing only a new test file
        mock_tool.return_value = True
        mock_status = MagicMock()
        mock_status.returncode = 0
        mock_status.stdout = "A  tests/test_new_feature.py"

        def run_side_effect(cmd, **kwargs):
            if cmd[1] == "status":
                return mock_status
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        if hasattr(orchestrator, "validate_tdd_compliance"):
            passed, msg = orchestrator.validate_tdd_compliance()
            assert passed is True
            assert "Red Phase" in msg
        else:
            pytest.fail("validate_tdd_compliance function missing in Orchestrator")

    @patch("check_protocol_compliance_mirror.check_tool_available")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_balanced_changes_passes(self, mock_run, mock_tool):
        """Verify that balanced code and test changes pass."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        mock_tool.return_value = True
        mock_status = MagicMock()
        mock_status.returncode = 0
        mock_status.stdout = "M  src/new_feature.py\nA  tests/test_new_feature.py"

        def run_side_effect(cmd, **kwargs):
            if cmd[1] == "status":
                return mock_status
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        if hasattr(orchestrator, "validate_tdd_compliance"):
            passed, msg = orchestrator.validate_tdd_compliance()
            assert passed is True
        else:
            pytest.fail("validate_tdd_compliance function missing in Orchestrator")
