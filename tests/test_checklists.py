import pytest
from pathlib import Path
from agent_harness.checklists import ChecklistManager

def test_checklist_manager_load(tmp_path):
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir()
    
    initialization_json = {
        "phases": [
            {
                "id": "test_phase",
                "name": "Test Phase",
                "status": "MANDATORY",
                "checks": [
                    {
                        "id": "check1",
                        "description": "True Check",
                        "type": "BLOCKER",
                        "validator": "always_true"
                    },
                    {
                        "id": "check2",
                        "description": "False Check",
                        "type": "WARNING",
                        "validator": "always_false"
                    }
                ]
            }
        ]
    }
    
    import json
    with open(checklist_dir / "test_phase.json", "w") as f:
        json.dump(initialization_json, f)
    
    manager = ChecklistManager(checklist_dir)
    manager.register_validator("always_true", lambda *args: (True, "OK"))
    manager.register_validator("always_false", lambda *args: (False, "Failing"))
    
    passed, blockers, warnings = manager.run_phase("test_phase")
    
    assert passed is True
    assert len(blockers) == 0
    assert len(warnings) == 1
    assert "False Check" in warnings[0]

def test_checklist_manager_block(tmp_path):
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir()
    
    initialization_json = {
        "phases": [
            {
                "id": "test_phase",
                "name": "Test Phase",
                "status": "MANDATORY",
                "checks": [
                    {
                        "id": "check1",
                        "description": "Blocking Check",
                        "type": "BLOCKER",
                        "validator": "always_false"
                    }
                ]
            }
        ]
    }
    
    import json
    with open(checklist_dir / "test_phase.json", "w") as f:
        json.dump(initialization_json, f)
    
    manager = ChecklistManager(checklist_dir)
    manager.register_validator("always_false", lambda *args: (False, "Blocked!"))
    
    passed, blockers, warnings = manager.run_phase("test_phase")
    
    assert passed is False
    assert len(blockers) == 1
    assert "Blocking Check" in blockers[0]
