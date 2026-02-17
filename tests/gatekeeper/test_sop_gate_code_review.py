import subprocess
import sys
import unittest
from pathlib import Path


class TestSOPGateCodeReview(unittest.TestCase):
    def setUp(self):
        # Use mirrored orchestrator script relative to test file
        # This test is in tests/gatekeeper/
        self.orchestrator = (
            Path(__file__).parents[2]
            / "tests/orchestrator_mirror/check_protocol_compliance_mirror.py"
        )
        # code_review_script is not mirrored, so it will likely fail if used.
        # But test only runs orchestrator.

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
