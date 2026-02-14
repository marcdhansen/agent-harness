from unittest.mock import MagicMock, patch

import pytest
from agent_harness.compliance import check_branch_info, get_active_issue_id


@pytest.mark.parametrize(
    "branch_name, expected_id",
    [
        ("agent/agent-harness-abc-fix", "agent-harness-abc"),
        ("feature/lightrag-xyz-logic", "lightrag-xyz"),
        ("chore/beads-123-update", "beads-123"),
        ("agent/agent-gbv.13-hardening", "agent-gbv.13"),
        ("bugfix/12345-fix", "12345"),
        ("agent/my-project-abc", "my-project-abc"),
    ],
)
def test_get_active_issue_id_flexible(branch_name, expected_id):
    with patch("subprocess.check_output") as mock_git:
        mock_git.return_value = branch_name
        assert get_active_issue_id() == expected_id


@pytest.mark.parametrize(
    "branch_name, expected_is_feature",
    [
        ("main", False),
        ("master", False),
        ("develop", False),
        ("origin/main", False),
        ("agent/feature-1", True),
        ("custom/branch-abc", True),
        ("feature-branch", False),  # No slash
    ],
)
def test_check_branch_info_flexible(branch_name, expected_is_feature):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=branch_name)
        _, is_feature = check_branch_info()
        assert is_feature == expected_is_feature
