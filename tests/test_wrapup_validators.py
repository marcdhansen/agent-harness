import pytest
from pathlib import Path
from agent_harness.compliance import check_wrapup_indicator_symmetry, check_wrapup_exclusivity


def test_check_wrapup_indicator_symmetry_missing_flag(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Simulate SOP complete but 🏁 missing
    (tmp_path / "debrief.md").write_text("Session ID: test-session\nPR: github.com/pull/1")
    (tmp_path / ".reflection_input.json").write_text("{}")

    # Mock get_active_issue_id to return test-id which is in debrief
    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "test-session")

    passed, msg = check_wrapup_indicator_symmetry()
    assert not passed
    assert "missing" in msg


def test_check_wrapup_indicator_symmetry_invalid_usage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Simulate 🏁 present but SOP incomplete (missing reflection)
    (tmp_path / "debrief.md").write_text("🏁 Session ID: test-session\nPR: github.com/pull/1")

    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "test-session")

    passed, msg = check_wrapup_indicator_symmetry()
    assert not passed
    assert "incomplete" in msg


def test_check_wrapup_indicator_symmetry_valid(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Simulate SOP complete and 🏁 present
    (tmp_path / "debrief.md").write_text("🏁 Session ID: test-session\nPR: github.com/pull/1")
    (tmp_path / ".reflection_input.json").write_text("{}")

    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "test-session")

    passed, msg = check_wrapup_indicator_symmetry()
    assert passed


def test_check_wrapup_exclusivity_forbidden(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Simulate 🏁 in ROADMAP.md
    (tmp_path / "ROADMAP.md").write_text("Next steps: 🏁")

    # Mock issue ID to something else
    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "some-other-task")

    passed, msg = check_wrapup_exclusivity()
    assert not passed
    assert "forbidden" in msg


def test_check_wrapup_exclusivity_allowed_for_b9y(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Simulate 🏁 in ROADMAP.md but we are on the task to implement it
    (tmp_path / "ROADMAP.md").write_text("Implementing 🏁 in this task")

    monkeypatch.setattr("agent_harness.compliance.get_active_issue_id", lambda: "agent-harness-b9y")

    passed, msg = check_wrapup_exclusivity()
    assert passed
