import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util

# Add project root to sys.path FIRST and ensure it's prioritized
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from the script directly - use absolute path to avoid any confusion
module_path = os.path.join(project_root, "check_protocol_compliance.py")
spec = importlib.util.spec_from_file_location("check_protocol_compliance", module_path)
if spec and spec.loader:
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
else:
    import check_protocol_compliance as cli


class TestAgentFriendlyCli(unittest.TestCase):
    def setUp(self):
        # Clear env vars that might interfere
        for var in ["HARNESS_MODE", "HARNESS_ISSUE_ID", "HARNESS_NON_INTERACTIVE"]:
            if var in os.environ:
                del os.environ[var]

    @patch.object(cli, "is_interactive")
    @patch.object(cli, "load_config")
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
            default="default_val",
        )
        self.assertEqual(val, "cli_val")

        # Test 2: Env var priority
        val = cli.get_value(
            arg_value=None,
            env_var="HARNESS_MODE",
            config_key="mode",
            prompt="Prompt",
            default="default_val",
        )
        self.assertEqual(val, "env_val")


if __name__ == "__main__":
    unittest.main()
