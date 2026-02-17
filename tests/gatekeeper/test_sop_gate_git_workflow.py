"""
Test suite for PR Merge Compliance SOP gate enforcement.
# Gate: docs/sop/git-workflow.md (Lines: 50, 54, 55, 56)
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


class TestGatePRMerge:
    """Tests for mandatory rebase-and-squash enforcement."""

    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_merge_commit_blocked(self, mock_run):
        """Verify that merge commits are blocked."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        # Mock git log showing a merge commit
        def run_side_effect(cmd, **kwargs):
            if "--merges" in cmd:
                return MagicMock(returncode=0, stdout="a1b2c3d Merge branch 'main' into feature")
            if "origin/main..HEAD" in cmd:
                return MagicMock(returncode=0, stdout="a1b2c3d commit 1")
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        passed, errors = orchestrator.validate_atomic_commits()
        assert passed is False
        assert any("Merge commits not allowed" in err for err in errors)

    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_multiple_commits_blocked(self, mock_run):
        """Verify that multiple commits are blocked (require squash)."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        # Mock git log showing 2 commits
        def run_side_effect(cmd, **kwargs):
            if "origin/main..HEAD" in cmd and "--merges" not in cmd:
                return MagicMock(returncode=0, stdout="a1b2c3d commit 1\ne4f5g6h commit 2")
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        passed, errors = orchestrator.validate_atomic_commits()
        assert passed is False
        assert any("Multiple commits detected" in err for err in errors)

    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_atomic_commit_passes(self, mock_run):
        """Verify that a single atomic commit with issue ID passes."""
        if orchestrator is None:
            pytest.skip("Orchestrator not found")

        # Mock git log showing 1 commit with ID
        def run_side_effect(cmd, **kwargs):
            if "origin/main..HEAD" in cmd and "--merges" not in cmd:
                return MagicMock(returncode=0, stdout="a1b2c3d feat(core): unit tests [issue-123]")
            if "--pretty=%B" in cmd:
                return MagicMock(returncode=0, stdout="feat(core): unit tests [issue-123]")
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = run_side_effect

        passed, errors = orchestrator.validate_atomic_commits()
        assert passed is True
        assert len(errors) == 0
