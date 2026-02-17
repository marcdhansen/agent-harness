import unittest
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from the script directly
import check_protocol_compliance as cli

class TestAgentFriendlyCli(unittest.TestCase):
    def setUp(self):
        # Clear env vars that might interfere
        for var in ["HARNESS_MODE", "HARNESS_ISSUE_ID", "HARNESS_NON_INTERACTIVE"]:
            if var in os.environ:
                del os.environ[var]

    @patch("check_protocol_compliance.is_interactive")
    @patch("check_protocol_compliance.load_config")
    def test_get_value_priority(self, mock_load_config, mock_interactive):
        mock_interactive.return_value = False
        mock_load_config.return_value = {"mode": "config_val"}
        
        # Test 1: CLI arg priority
        os.environ["HARNESS_MODE"] = "env_val"
        val = cli.get_value(
            arg_value="cli_val",
            env_var="HARNESS_MODE",
            config_key="mode",
            prompt="Prompt",
            default="default_val"
        )
        self.assertEqual(val, "cli_val")

        # Test 2: Env var priority
        val = cli.get_value(
            arg_value=None,
            env_var="HARNESS_MODE",
            config_key="mode",
            prompt="Prompt",
            default="default_val"
        )
        self.assertEqual(val, "env_val")

if __name__ == "__main__":
    unittest.main()
