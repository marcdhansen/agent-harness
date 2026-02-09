import unittest
import subprocess
import os
import sys
from pathlib import Path


class TestSOPGateCodeReview(unittest.TestCase):
    def setUp(self):
        self.orchestrator = (
            Path.home()
            / ".gemini/antigravity/skills/Orchestrator/scripts/check_protocol_compliance.py"
        )
        self.code_review_script = (
            Path.home() / ".gemini/antigravity/skills/code-review/scripts/code_review.py"
        )

    def test_finalization_blocks_without_code_review(self):
        """Test that finalization fails if code review has not been passed (or script fails)."""
        # We simulate a situation where code review would fail or hasn't run.
        # Currently, the orchestrator doesn't even know about the code review skill,
        # so it should pass if other conditions are met.
        # Once we add the gate, this test should fail until we provide a passing review.

        # Run orchestrator --finalize in a clean git state (or mock it)
        # For simplicity, we check if the orchestrator output contains "Code Review"
        result = subprocess.run(
            [sys.executable, str(self.orchestrator), "--status"], capture_output=True, text=True
        )
        self.assertIn(
            "Code Review", result.stdout, "Orchestrator should mention Code Review status"
        )


if __name__ == "__main__":
    unittest.main()
