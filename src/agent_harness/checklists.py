import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

class ChecklistCheck:
    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.description = data["description"]
        self.type = data["type"]  # BLOCKER or WARNING
        self.validator_name = data["validator"]
        self.args = data.get("args", [])

class ChecklistPhase:
    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.name = data["name"]
        self.status = data["status"]  # MANDATORY or OPTIONAL
        self.description = data.get("description", "")
        self.checks = [ChecklistCheck(c) for c in data.get("checks", [])]

class ChecklistManager:
    def __init__(self, checklist_dir: Path):
        self.checklist_dir = checklist_dir
        self.validators: Dict[str, Callable] = {}

    def register_validator(self, name: str, func: Callable):
        self.validators[name] = func

    def load_checklist(self, name: str) -> Optional[ChecklistPhase]:
        path = self.checklist_dir / f"{name}.json"
        if not path.exists():
            return None
        
        with open(path, "r") as f:
            data = json.load(f)
            # The schema has a 'phases' array at the top level
            if "phases" in data and len(data["phases"]) > 0:
                return ChecklistPhase(data["phases"][0])
        return None

    def run_check(self, check: ChecklistCheck) -> Tuple[bool, str]:
        if check.validator_name not in self.validators:
            return False, f"Validator '{check.validator_name}' not registered"
        
        validator = self.validators[check.validator_name]
        try:
            # We assume validators return (bool, str) or just bool
            result = validator(*check.args)
            if isinstance(result, tuple):
                return result
            return result, "Check passed" if result else "Check failed"
        except Exception as e:
            return False, f"Error running validator '{check.validator_name}': {str(e)}"

    def run_phase(self, phase_name: str) -> Tuple[bool, List[str], List[str]]:
        phase = self.load_checklist(phase_name)
        if not phase:
            return False, [f"Checklist '{phase_name}' not found"], []
        
        blockers = []
        warnings = []
        
        for check in phase.checks:
            passed, msg = self.run_check(check)
            if not passed:
                if check.type == "BLOCKER":
                    blockers.append(f"{check.description}: {msg}")
                else:
                    warnings.append(f"{check.description}: {msg}")
        
        passed = (len(blockers) == 0)
        return passed, blockers, warnings
