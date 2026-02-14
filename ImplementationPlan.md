# Implementation Plan - Hardening Agent Harness (agent-gbv.13)

## Problem

Agent harnesses are vulnerable to bypass attempts via prompt injection, tool evasion, and state manipulation. Current implementation in `InnerHarness` is minimalist and lacks active enforcement.

## Proposed Changes

1. **Core Tool Registry Hardening**:
    * Implement an explicit `ToolRegistry` that validates tools before execution.
    * Ensure no tools outside the whitelist can be invoked.

2. **Prompt Engineering Defense-in-Depth**:
    * Implement "Sandwich Constraints" in `InnerHarness`.
    * Add "Anti-Jailbreak" patterns to the system prompt.
    * Enforce a "Tool-Only" mandate in the prompt instructions.

3. **Behavioral Monitoring & Auditing**:
    * Implement `ToolAuditor` to log all tool calls and detect suspicious patterns (e.g., excessive bash usage, sensitive file access).
    * Implement `EscapeDetector` to scan for bypass keywords in user input and agent responses.

4. **State Validation**:
    * Introduce basic Pydantic validation for internal agent states to prevent out-of-bounds transitions.

## Blast Radius Analysis

* **src/agent_harness/inner.py**: Primary impact. The `InnerHarness` class will be updated to use the new security layers.
* **src/agent_harness/state.py**: Minor impact. Updating state definitions to support validation.
* **New files**: `src/agent_harness/security.py` (or similar) to house the hardening logic.
* **Backward Compatibility**: The new security features should be opt-in or transparent for existing users of `InnerHarness`.

## Verification Plan

1. **Red Team Unit Tests**:
   * Test various prompt injection strings (e.g., "Ignore previous instructions").
   * Test tool evasion attempts (e.g., "Tell me the file content instead of using read").
   * Verify `ToolAuditor` catches suspicious bash commands.
2. **Integration Tests**:
   * Run a full loop with a simulated "malicious" agent and verify it's blocked.

## Tasks

* [x] Create `src/agent_harness/security.py` with `ToolAuditor` and `EscapeDetector`.
* [x] Update `InnerHarness` in `src/agent_harness/inner.py` to incorporate security layers.
* [x] Implement hardened prompt templates.
* [x] Add comprehensive tests for bypass prevention.

## Status

* **agent-gbv.13**: Work completed, PR #27 created, issue set to `in_review`.

## Completion Note

Layer 2 and Layer 3 security measures have been successfully deployed. The harness now requires an active session, audits all tool calls, and scans for escape attempts. This implementation plan is now closed.
