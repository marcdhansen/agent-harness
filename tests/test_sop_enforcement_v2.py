import json
import subprocess

from agent_harness.compliance import (
    check_beads_pr_sync,
    check_no_separate_review_issues,
)


def test_check_no_separate_review_issues_violation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Mock get_active_issue_id
    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "issue-123")

    # Mock bd list --status open to return a separate review issue
    class MockResult:
        def __init__(self, stdout, returncode=0):
            self.stdout = stdout
            self.returncode = returncode

    def mock_run(args, **kwargs):
        if args[:3] == ["bd", "list", "--status"]:
            return MockResult("issue-123: main task\nissue-456: PR Review: issue-123")
        return MockResult("")

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr("agent_harness.compliance.check_tool_available", lambda x: True)

    passed, msg = check_no_separate_review_issues()
    assert not passed
    assert "Separate review issues detected" in msg
    assert "issue-456" in msg


def test_check_no_separate_review_issues_pass(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "issue-123")

    def mock_run(args, **kwargs):
        if args[:3] == ["bd", "list", "--status"]:
            return MockResult("issue-123: main task\nissue-789: some other task")
        return MockResult("")

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr("agent_harness.compliance.check_tool_available", lambda x: True)

    passed, msg = check_no_separate_review_issues()
    assert passed
    assert "No separate PR review issues detected" in msg


def test_check_beads_pr_sync_missing_comment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "issue-123")
    monkeypatch.setattr(
        "agent_harness.compliance.check_branch_info", lambda: ("agent-harness/issue-123", True)
    )
    monkeypatch.setattr("agent_harness.compliance.check_tool_available", lambda x: True)

    def mock_run(args, **kwargs):
        if args[:3] == ["gh", "pr", "view"]:
            return MockResult(
                json.dumps(
                    {
                        "title": "[issue-123] Fix things",
                        "body": "References issue-123",
                        "url": "https://github.com/org/repo/pull/1",
                    }
                )
            )
        if args[:3] == ["bd", "show", "issue-123"]:
            # No PR URL in the show output
            return MockResult("issue-123 details\nNo comments yet.")
        return MockResult("")

    monkeypatch.setattr(subprocess, "run", mock_run)

    passed, msg = check_beads_pr_sync()
    assert not passed
    assert "must contain a comment with the PR URL" in msg


def test_check_beads_pr_sync_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "issue-123")
    monkeypatch.setattr(
        "agent_harness.compliance.check_branch_info", lambda: ("agent-harness/issue-123", True)
    )
    monkeypatch.setattr("agent_harness.compliance.check_tool_available", lambda x: True)

    def mock_run(args, **kwargs):
        if args[:3] == ["gh", "pr", "view"]:
            return MockResult(
                json.dumps(
                    {
                        "title": "[issue-123] Fix things",
                        "body": "References issue-123",
                        "url": "https://github.com/org/repo/pull/1",
                    }
                )
            )
        if args[:3] == ["bd", "show", "issue-123"]:
            return MockResult("issue-123 details\nPR: https://github.com/org/repo/pull/1")
        return MockResult("")

    monkeypatch.setattr(subprocess, "run", mock_run)

    passed, msg = check_beads_pr_sync()
    assert passed
    assert "properly synchronized" in msg


class MockResult:
    def __init__(self, stdout, returncode=0):
        self.stdout = stdout
        self.returncode = returncode
