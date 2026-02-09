"""
Test suite for Orchestrator atomic commit validation.

Following the pattern from agent-harness-a5r (Turbo Mode test suite),
this module verifies that the Orchestrator correctly detects and blocks
non-atomic commits and merge commits during finalization.

Test Cases:
1. test_single_atomic_commit_passes - Valid case with 1 commit
2. test_multiple_commits_blocked - Multiple commits should be rejected
3. test_merge_commit_blocked - Merge commits should be rejected
4. test_missing_issue_id_blocked - Missing Beads issue ID should be rejected
5. test_valid_commit_message_format - Valid conventional commit format

Run with: pytest tests/test_orchestrator_atomic_commits.py -v
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add Orchestrator scripts to path
sys.path.insert(0, str(Path.home() / ".gemini/antigravity/skills/Orchestrator/scripts"))

from check_protocol_compliance import validate_atomic_commits


class TestAtomicCommitValidation:
    """Test suite for atomic commit validation logic."""

    @patch("check_protocol_compliance.subprocess.run")
    def test_single_atomic_commit_passes(self, mock_run):
        """Test that a single atomic commit with valid format passes all checks."""
        # Mock git log for commit count (1 commit)
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        mock_count_result.stdout = "abc1234 feat(auth): add JWT validation [agent-harness-v0o]\\n"

        # Mock git log for merge commits (none)
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = ""

        # Mock git log for commit message
        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout = "feat(auth): add JWT validation [agent-harness-v0o]\\n\\nImplemented token validation with expiry checks."

        mock_run.side_effect = [mock_count_result, mock_merge_result, mock_msg_result]

        is_valid, errors = validate_atomic_commits()

        assert is_valid is True
        assert len(errors) == 0

    @patch("check_protocol_compliance.subprocess.run")
    def test_multiple_commits_blocked(self, mock_run):
        """Test that multiple commits are detected and blocked."""
        # Mock git log showing 3 commits
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        mock_count_result.stdout = (
            "abc1234 feat(auth): add validation\n"
            "def5678 fix(auth): update tests\n"
            "ghi9012 docs: update README\n"
        )

        # Mock git log for merge commits (none)
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = ""

        # Note: With 3 commits, the function won't check commit message
        # so we don't need a third mock

        mock_run.side_effect = [mock_count_result, mock_merge_result]

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert len(errors) > 0
        # Check that errors mention multiple commits
        error_text = " ".join(errors)
        assert "Multiple commits" in error_text or "Squash required" in error_text

    @patch("check_protocol_compliance.subprocess.run")
    def test_merge_commit_blocked(self, mock_run):
        """Test that merge commits are detected and blocked."""
        # Mock git log for commit count (1 commit)
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        mock_count_result.stdout = "abc1234 Merge pull request #2\\n"

        # Mock git log showing merge commit
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = "abc1234 Merge pull request #2 from feature/test\\n"

        # Mock commit message (for single commit check)
        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout = "Merge pull request #2 from feature/test"

        mock_run.side_effect = [mock_count_result, mock_merge_result, mock_msg_result]

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "Merge commits not allowed" in error_text
        assert "rebase" in error_text.lower()

    @patch("check_protocol_compliance.subprocess.run")
    def test_missing_issue_id_blocked(self, mock_run):
        """Test that commits without Beads issue ID are blocked."""
        # Mock git log for commit count (1 commit)
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        mock_count_result.stdout = "abc1234 feat(auth): add validation\\n"

        # Mock git log for merge commits (none)
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = ""

        # Mock commit message WITHOUT issue ID
        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout = "feat(auth): add JWT validation\\n\\nNo issue ID here."

        mock_run.side_effect = [mock_count_result, mock_merge_result, mock_msg_result]

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert any("Beads issue ID" in err for err in errors)
        assert any("[issue-id]" in err for err in errors)

    @patch("check_protocol_compliance.subprocess.run")
    def test_valid_commit_message_format(self, mock_run):
        """Test that valid conventional commit format is accepted."""
        # Mock git log for commit count (1 commit)
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        mock_count_result.stdout = "abc1234 chore(docs): update README [agent-harness-v0o]\\n"

        # Mock git log for merge commits (none)
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = ""

        # Mock valid commit message
        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout = "chore(docs): update README [agent-harness-v0o]"

        mock_run.side_effect = [mock_count_result, mock_merge_result, mock_msg_result]

        is_valid, errors = validate_atomic_commits()

        assert is_valid is True
        assert len(errors) == 0

    @patch("check_protocol_compliance.subprocess.run")
    def test_invalid_commit_message_format(self, mock_run):
        """Test that invalid commit message format is rejected."""
        # Mock git log for commit count (1 commit)
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        mock_count_result.stdout = "abc1234 Added some changes [agent-harness-v0o]\\n"

        # Mock git log for merge commits (none)
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = ""

        # Mock INVALID commit message format
        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout = "Added some changes [agent-harness-v0o]"

        mock_run.side_effect = [mock_count_result, mock_merge_result, mock_msg_result]

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert any("conventional format" in err for err in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
