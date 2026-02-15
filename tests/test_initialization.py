"""Tests for initialization validation in the Orchestrator."""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the orchestrator script path to sys.path
orchestrator_path = Path(__file__).parent / "orchestrator_mirror"
sys.path.append(str(orchestrator_path))

# Import the functions to test (they might not exist yet)
try:
    import check_protocol_compliance as orchestrator
except ImportError:
    orchestrator = None


class TestInitializationValidation(unittest.TestCase):
    """Test the initialization validation logic."""

    def setUp(self):
        if orchestrator is None:
            self.skipTest("Orchestrator script not found or importable")

    @patch("subprocess.run")
    def test_check_tool_version_success(self, mock_run):
        """Test tool version check success."""
        # Mock git --version output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.34.1"
        mock_run.return_value = mock_result

        # We need to define this function in the orchestrator first
        if hasattr(orchestrator, "check_tool_version"):
            passed, msg = orchestrator.check_tool_version("git", "2.25.0", "--version")
            self.assertTrue(passed)
            self.assertIn("2.34.1", msg)

    @patch("subprocess.run")
    def test_check_tool_version_failure_too_old(self, mock_run):
        """Test tool version check failure when version is too old."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.10.0"
        mock_run.return_value = mock_result

        if hasattr(orchestrator, "check_tool_version"):
            passed, msg = orchestrator.check_tool_version("git", "2.25.0", "--version")
            self.assertFalse(passed)
            self.assertIn("too old", msg.lower())

    @patch("subprocess.run")
    def test_check_tool_version_malformed_output(self, mock_run):
        """Test tool version check with malformed output."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "no version info here"
        mock_run.return_value = mock_result

        if hasattr(orchestrator, "check_tool_version"):
            passed, msg = orchestrator.check_tool_version("git", "2.25.0", "--version")
            self.assertFalse(passed)
            self.assertIn("Could not parse", msg)

    @patch("pathlib.Path.exists")
    def test_check_workspace_integrity_success(self, mock_exists):
        """Test workspace integrity check success."""
        mock_exists.return_value = True

        if hasattr(orchestrator, "check_workspace_integrity"):
            passed, missing = orchestrator.check_workspace_integrity()
            self.assertTrue(passed)
            self.assertEqual(len(missing), 0)

    @patch("validators.git_validator.Path")
    def test_check_workspace_integrity_failure(self, mock_path):
        """Test workspace integrity check failure."""
        # Mock some files missing
        mock_git = MagicMock()
        mock_git.exists.return_value = True

        mock_agent = MagicMock()
        mock_agent.exists.return_value = False
        mock_agent.__str__.return_value = ".agent"

        mock_beads = MagicMock()
        mock_beads.exists.return_value = True

        def path_side_effect(name):
            if name == ".git":
                return mock_git
            if name == ".agent":
                return mock_agent
            if name == ".beads":
                return mock_beads
            return MagicMock()

        mock_path.side_effect = path_side_effect

        if hasattr(orchestrator, "check_workspace_integrity"):
            passed, missing = orchestrator.check_workspace_integrity()
            self.assertFalse(passed)
            self.assertIn(".agent", missing)


if __name__ == "__main__":
    unittest.main()
