"""
Example: Basic session using inner harness for simple tasks.

This demonstrates the minimal Pi Mono-style approach with just 4 tools.
"""

# from agent_harness import InnerHarness

# Example usage (requires an LLM client):
#
# from openai import OpenAI
#
# client = OpenAI()
#
# def invoke_wrapper(messages, tools=None):
#     return client.chat.completions.create(
#         model="gpt-4o",
#         messages=messages,
#         tools=tools,
#     ).choices[0].message
#
# class LLMWrapper:
#     def invoke(self, messages, tools=None):
#         return invoke_wrapper(messages, tools)
#
# harness = InnerHarness(llm_client=LLMWrapper())
# result = harness.run("Create a hello world Python script in /tmp/hello.py")
# print(result)

if __name__ == "__main__":
    print("See comments in this file for usage example.")
    print("Requires an LLM client (e.g., OpenAI, Anthropic, Ollama)")
