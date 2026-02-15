import json
from pathlib import Path

from agent_harness.checklists import ChecklistManager


def test_retrospective_blockers():
    """Verify that all checks in retrospective.json are BLOCKERs."""
    project_root = Path.cwd()
    retrospective_path = project_root / ".agent/rules/checklists/retrospective.json"

    with open(retrospective_path) as f:
        data = json.load(f)

    for phase in data["phases"]:
        if phase["id"] == "retrospective":
            for check in phase["checks"]:
                assert check["type"] == "BLOCKER", f"Check {check['id']} should be BLOCKER"


def test_retrospective_passed_false_on_blocker():
    """Verify that run_phase returns passed=False if any check fails."""
    project_root = Path.cwd()
    checklist_dir = project_root / ".agent/rules/checklists"

    manager = ChecklistManager(checklist_dir)

    # Mocking all validators to return False to test blocker enforcement
    # We need to get the list of unique validators from the JSON
    with open(checklist_dir / "retrospective.json") as f:
        data = json.load(f)

    validators = set()
    for phase in data["phases"]:
        for check in phase["checks"]:
            validators.add(check["validator"])

    for v in validators:
        manager.register_validator(v, lambda *args, **kwargs: (False, "Failing for test"))

    passed, blockers, warnings = manager.run_phase("retrospective")

    assert passed is False
    assert len(blockers) > 0
    assert len(warnings) == 0  # Since all are blockers now
