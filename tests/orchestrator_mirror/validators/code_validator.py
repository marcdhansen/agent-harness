import subprocess
from pathlib import Path


def validate_tdd_compliance() -> tuple[bool, str]:
    """Validate that code changes are preceded by or accompanied by test changes.

    Enforces the 'Spec-Driven TDD' rule from tdd-workflow.md.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return False, "Failed to get git status"

        lines = result.stdout.strip().split("\n")
        if not lines or (len(lines) == 1 and not lines[0]):
            return True, "No changes detected"

        code_files = []
        test_files = []

        # Extensions that count as code
        code_exts = {".py", ".js", ".ts", ".go", ".c", ".cpp", ".java"}

        for line in lines:
            if len(line) < 4:
                continue
            _status = line[:2].strip()
            file_path = line[3:].strip()

            ext = Path(file_path).suffix
            if ext in code_exts:
                if "test" in file_path.lower() or file_path.startswith("tests/"):
                    test_files.append(file_path)
                else:
                    code_files.append(file_path)

        if not code_files and test_files:
            return (
                True,
                f"Red Phase: Test stubs detected without implementation ({', '.join(test_files)})",
            )

        if code_files and not test_files:
            return (
                False,
                f"TDD Violation: Implementation changes detected without corresponding tests: {', '.join(code_files)}",
            )

        return True, "TDD compliance verified (Balanced changes)"

    except Exception as e:
        return False, f"TDD validation error: {e}"
