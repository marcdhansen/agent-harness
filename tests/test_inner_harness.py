"""Tests for InnerHarness - the minimal Pi Mono-style agent loop."""

import pytest

from agent_harness.inner import (
    BashTool,
    EditTool,
    InnerHarness,
    ReadTool,
    Tool,
    WriteTool,
)


class TestCoreTools:
    """Test the 4 core tools."""

    def test_read_tool_exists(self):
        tool = ReadTool()
        assert tool.name == "read"
        assert "file" in tool.description.lower()

    def test_write_tool_exists(self):
        tool = WriteTool()
        assert tool.name == "write"
        assert "file" in tool.description.lower()

    def test_edit_tool_exists(self):
        tool = EditTool()
        assert tool.name == "edit"
        assert "old_content" in tool.description.lower()

    def test_bash_tool_exists(self):
        tool = BashTool()
        assert tool.name == "bash"
        assert "command" in tool.description.lower()

    def test_bash_tool_executes_command(self):
        tool = BashTool()
        result = tool.execute("echo hello")
        assert "hello" in result

    def test_bash_tool_handles_error(self):
        tool = BashTool()
        result = tool.execute("exit 1")
        # Should not raise, just return output
        assert isinstance(result, str)


class TestInnerHarness:
    """Test InnerHarness initialization and configuration."""

    def test_default_tools(self):
        """Harness should have 4 default tools."""

        # Create a mock LLM
        class MockLLM:
            def invoke(self, messages, **kwargs):
                class Response:
                    content = "Done"
                    tool_calls = None

                return Response()

        harness = InnerHarness(llm_client=MockLLM(), hardened=False)
        assert len(harness.tools) == 4
        assert "read" in harness.tools
        assert "write" in harness.tools
        assert "edit" in harness.tools
        assert "bash" in harness.tools

    def test_custom_tools(self):
        """Harness should accept custom tools."""

        class CustomTool(Tool):
            @property
            def name(self):
                return "custom"

            @property
            def description(self):
                return "A custom tool"

            def execute(self, **kwargs):
                return "custom result"

        class MockLLM:
            def invoke(self, messages, **kwargs):
                class Response:
                    content = "Done"
                    tool_calls = None

                return Response()

        harness = InnerHarness(llm_client=MockLLM(), tools=[CustomTool()])
        assert len(harness.tools) == 1
        assert "custom" in harness.tools

    def test_custom_system_prompt(self):
        """Harness should accept custom system prompt."""

        class MockLLM:
            def invoke(self, messages, **kwargs):
                class Response:
                    content = "Done"
                    tool_calls = None

                return Response()

        harness = InnerHarness(llm_client=MockLLM(), system_prompt="Custom prompt", hardened=False)
        assert harness.system_prompt == "Custom prompt"

    def test_run_no_tools(self):
        """Run should return when LLM doesn't request tools."""

        class MockLLM:
            def invoke(self, messages, **kwargs):
                class Response:
                    content = "Task complete!"
                    tool_calls = None

                return Response()

        harness = InnerHarness(llm_client=MockLLM(), hardened=False)
        result = harness.run("Do something")
        assert result == "Task complete!"

    def test_max_iterations_limit(self):
        """Run should stop at max iterations."""
        call_count = 0

        class MockLLM:
            def invoke(self, messages, **kwargs):
                nonlocal call_count
                call_count += 1

                class ToolCall:
                    id = "tc1"

                    class function:
                        name = "bash"
                        arguments = '{"command": "echo hi"}'

                class Response:
                    content = "Using tool"
                    tool_calls = [ToolCall()]

                return Response()

        harness = InnerHarness(llm_client=MockLLM(), hardened=False)
        result = harness.run("Loop forever", max_iterations=3)
        assert "Max iterations" in result
        assert call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
