# Task: Hardening Agent Harnesses - Preventing Bypass Attempts (agent-gbv.13)

## Objective

Implement architectural and prompt-level defenses to prevent AI agents from bypassing harness constraints.

## TODO

- [x] Implement `ToolAuditor` for tracking tool usage patterns
- [x] Implement `EscapeDetector` for identifying jailbreak attempts
- [x] Harden `InnerHarness` system prompts using sandwich constraints
- [x] Create red team test cases for bypass prevention
- [x] Implement Git-level policy enforcement (pre-commit hooks)
- [x] (Optional) Migrate state to Pydantic for strict validation
