"""
InnerHarness: Minimal Pi Mono-style agent loop.

This provides a simple, stateless agent loop with minimal overhead.
For users who don't need full SMP compliance, this is the entry point.
"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Base class for inner harness tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for LLM invocation."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM context."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool and return result."""
        ...


class ReadTool(Tool):
    """Read file contents."""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Args: path (str)"

    def execute(self, path: str) -> str:
        try:
            with open(path) as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"


class WriteTool(Tool):
    """Write content to a file."""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "Write content to a file. Args: path (str), content (str)"

    def execute(self, path: str, content: str) -> str:
        try:
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file: {e}"


class EditTool(Tool):
    """Edit a file by replacing content."""

    @property
    def name(self) -> str:
        return "edit"

    @property
    def description(self) -> str:
        return "Edit a file by replacing old_content with new_content. Args: path (str), old_content (str), new_content (str)"

    def execute(self, path: str, old_content: str, new_content: str) -> str:
        try:
            with open(path) as f:
                content = f.read()
            if old_content not in content:
                return f"Error: old_content not found in {path}"
            content = content.replace(old_content, new_content, 1)
            with open(path, "w") as f:
                f.write(content)
            return f"Successfully edited {path}"
        except Exception as e:
            return f"Error editing file: {e}"


class BashTool(Tool):
    """Execute bash commands."""

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return "Execute a bash command. Args: command (str)"

    def execute(self, command: str) -> str:
        import subprocess

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = result.stdout + result.stderr
            return output[:4000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: command timed out after 60 seconds"
        except Exception as e:
            return f"Error executing command: {e}"


DEFAULT_SYSTEM_PROMPT = """You are a helpful coding assistant. You have access to tools for reading, writing, and editing files, as well as executing bash commands.

When given a task:
1. First understand what needs to be done
2. Use the read tool to examine relevant files
3. Use write or edit tools to make changes
4. Use bash to run tests or verify your work
5. When the task is complete, provide a summary

Always verify your changes work before finishing. Be concise in your responses."""


class InnerHarness:
    """
    Minimal Pi Mono-style agent loop.

    No orchestration, no checkpointing, no compliance checks.
    Just: prompt → LLM → tools → repeat.

    Example:
        harness = InnerHarness(llm_client=my_openai_client)
        result = harness.run("Add a factorial function to utils.py")
    """

    CORE_TOOLS = [ReadTool(), WriteTool(), EditTool(), BashTool()]

    def __init__(
        self,
        llm_client: Any,
        tools: list[Tool] | None = None,
        system_prompt: str | None = None,
    ):
        """
        Initialize the inner harness.

        Args:
            llm_client: Any LLM client with an invoke() method that accepts messages
                       and returns a response with optional tool_calls.
            tools: List of Tool instances. Defaults to CORE_TOOLS (read, write, edit, bash).
            system_prompt: Custom system prompt. Defaults to minimal coding assistant prompt.
        """
        self.llm = llm_client
        self.tools = {t.name: t for t in (tools or self.CORE_TOOLS)}
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    def _build_tools_schema(self) -> list[dict]:
        """Build tool schema for LLM."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                },
            }
            for tool in self.tools.values()
        ]

    def _execute_tool(self, tool_call: Any) -> str:
        """Execute a tool call and return the result."""
        tool_name = tool_call.function.name
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"

        import json

        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            return f"Invalid tool arguments: {tool_call.function.arguments}"

        return self.tools[tool_name].execute(**args)

    def run(self, user_message: str, max_iterations: int = 50) -> str:
        """
        Run the simple agent loop until LLM stops requesting tools.

        Args:
            user_message: The task or question for the agent.
            max_iterations: Maximum tool invocations to prevent infinite loops.

        Returns:
            The final response from the LLM.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        for _ in range(max_iterations):
            response = self.llm.invoke(
                messages,
                tools=self._build_tools_schema(),
            )

            # Check if LLM wants to use tools
            if not hasattr(response, "tool_calls") or not response.tool_calls:
                return response.content  # Done - return final answer

            # Add assistant message with tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": response.tool_calls,
                }
            )

            # Execute each tool and add results
            for tool_call in response.tool_calls:
                result = self._execute_tool(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )

        return "Max iterations reached - task may be incomplete"
