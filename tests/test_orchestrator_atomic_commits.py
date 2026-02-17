# Mocking the Orchestrator environment
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add Orchestrator script path to sys.path
orchestrator_path = Path(__file__).parent / "orchestrator_mirror"
sys.path.insert(0, str(orchestrator_path))

from check_protocol_compliance_mirror import validate_atomic_commits  # noqa: E402


class TestAtomicCommitValidation:
    """Test suite for atomic commit validation logic."""

    def _setup_mocks(
        self,
        mock_run,
        base_branch="origin/main",
        commit_count=1,
        merge_commits="",
        commit_msg="feat(test): description [issue-id]",
    ):
        """Helper to setup mocks for the new multi-step base branch detection."""
        # 1. Base branch detection (origin/main)
        mock_verify_origin = MagicMock()
        if base_branch == "origin/main":
            mock_verify_origin.returncode = 0
        else:
            mock_verify_origin.returncode = 1

        # 2. Base branch detection (main) - only if origin/main failed
        mock_verify_main = MagicMock()
        if base_branch == "main":
            mock_verify_main.returncode = 0
        else:
            mock_verify_main.returncode = 1

        # 3. Base branch detection (master) - only if primary/secondary failed
        mock_verify_master = MagicMock()
        if base_branch == "master":
            mock_verify_master.returncode = 0
        else:
            mock_verify_master.returncode = 1

        # 4. Count commits
        mock_count_result = MagicMock()
        mock_count_result.returncode = 0
        if commit_count > 0:
            mock_count_result.stdout = (
                "\n".join(["abc" + str(i) + " msg" for i in range(commit_count)]) + "\n"
            )
        else:
            mock_count_result.stdout = ""

        # 5. Merge commits
        mock_merge_result = MagicMock()
        mock_merge_result.returncode = 0
        mock_merge_result.stdout = merge_commits

        # 6. Commit message (if count == 1)
        mock_msg_result = MagicMock()
        mock_msg_result.returncode = 0
        mock_msg_result.stdout = commit_msg

        side_effects = []
        # Detection sequence
        side_effects.append(mock_verify_origin)
        if base_branch != "origin/main":
            side_effects.append(mock_verify_main)
            if base_branch != "main":
                side_effects.append(mock_verify_master)

        # Execution sequence
        side_effects.append(mock_count_result)

        side_effects.append(mock_merge_result)
        if commit_count == 1:
            side_effects.append(mock_msg_result)

        mock_run.side_effect = side_effects

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_single_atomic_commit_passes(self, mock_run, mock_branch):
        """Test that a single atomic commit with valid format passes all checks."""
        mock_branch.return_value = ("agent-harness/test", True)
        self._setup_mocks(mock_run, base_branch="origin/main", commit_count=1)

        is_valid, errors = validate_atomic_commits()

        assert is_valid is True
        assert len(errors) == 0

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_multiple_commits_blocked(self, mock_run, mock_branch):
        """Test that multiple commits are detected and blocked."""
        mock_branch.return_value = ("agent-harness/test", True)
        self._setup_mocks(mock_run, base_branch="origin/main", commit_count=3)

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert any("Multiple commits detected" in err for err in errors)

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_merge_commit_blocked(self, mock_run, mock_branch):
        """Test that merge commits are detected and blocked."""
        mock_branch.return_value = ("agent-harness/test", True)
        self._setup_mocks(
            mock_run,
            base_branch="origin/main",
            commit_count=1,
            merge_commits="abc1234 Merge branch 'main' into feat\n",
        )

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        # Match either old or new error message
        all_errors = " ".join(errors)
        assert "Merge commits" in all_errors
        assert "forbidden" in all_errors or "not allowed" in all_errors

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_missing_issue_id_blocked(self, mock_run, mock_branch):
        """Test that commits without Beads issue ID are blocked."""
        mock_branch.return_value = ("agent-harness/test", True)
        self._setup_mocks(mock_run, commit_count=1, commit_msg="feat(auth): no issue id")

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert any("must include Beads issue ID" in err for err in errors)

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_valid_commit_message_format(self, mock_run, mock_branch):
        """Test that valid conventional commit format is accepted."""
        mock_branch.return_value = ("agent-harness/test", True)
        self._setup_mocks(
            mock_run, commit_count=1, commit_msg="chore(docs): update README [agent-harness-v0o]"
        )

        is_valid, errors = validate_atomic_commits()

        assert is_valid is True
        assert len(errors) == 0

    @patch("check_protocol_compliance_mirror.check_branch_info")
    @patch("check_protocol_compliance_mirror.subprocess.run")
    def test_invalid_commit_message_format(self, mock_run, mock_branch):
        """Test that invalid commit message format is rejected."""
        mock_branch.return_value = ("agent-harness/test", True)
        self._setup_mocks(
            mock_run, commit_count=1, commit_msg="Added some changes [agent-harness-v0o]"
        )

        is_valid, errors = validate_atomic_commits()

        assert is_valid is False
        assert any("conventional commit format" in err for err in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
