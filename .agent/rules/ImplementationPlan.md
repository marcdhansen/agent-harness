# 📋 Implementation Plan: agent-harness-2rn - Standardize structured JSON for reflection capture

## Objective

Standardize session reflections into a machine-readable `.reflection_input.json` file. This enables automated validation, consistent meta-learning, and reduces cognitive load during the retrospective phase.

## Proposed Changes

### 1. Schema Definition (`.agent/rules/reflection.schema.json`)

- Create a JSON Schema that defines the structure of the reflection.
- **Fields**:
  - `session_name` (string)
  - `outcome` (string: SUCCESS|PARTIAL|FAILURE)
  - `duration_hours` (number)
  - `success_metrics` (object/map)
  - `technical_learnings` (array of strings)
  - `challenges_overcome` (array of strings)
  - `protocol_issues` (array of strings)
  - `process_improvements` (array of strings)
  - `quantitative_results` (object/map)

### 2. Reflect Skill Enhancement (`~/.gemini/antigravity/skills/reflect/enhanced_reflection.py`)

- Update `EnhancedReflection._save_reflection` to also write the single session's data to `.reflection_input.json` in the workspace root.
- Ensure the output format matches the defined schema.
- Add basic validation logic if possible.

### 3. Orchestrator Enhancement (`~/.gemini/antigravity/skills/Orchestrator/scripts/check_protocol_compliance.py`)

- **Update `check_reflection_invoked()`**:
  - Change `reflection_paths` to include `.reflection_input.json`.
  - Add logic to parse the JSON and verify mandatory fields exist.
- **Improved Messaging**:
  - If `.reflection_input.json` is missing, provide the command to generate it (`/reflect`).

### 4. Testing (`tests/test_reflection_validation.py`)

- Implement test cases for:
  - Missing `.reflection_input.json`.
  - Malformed/Invalid JSON.
  - Valid JSON passing the check.

### 5. SOP Documentation

- Update `.agent/docs/SOP_COMPLIANCE_CHECKLIST.md` and `AGENTS.md` (if relevant) to include the new requirement.

## Verification

### Automated

- `pytest tests/test_reflection_validation.py`
- `check_protocol_compliance.py --finalize` in a test environment.

### Manual

- Run `/reflect` and verify `.reflection_input.json` is created and populated.
- Delete the file and verify `check_protocol_compliance.py --finalize` blocks.

## Blast Radius

- **Medium**: Affects the Finalization phase. If the JSON parsing fails or the schema is too restrictive, it could block PR creation.
- **Dependencies**: Depends on the existence of the Orchestrator and Reflect skills in their respective locations.

## Rollback Plan

- Revert changes to `check_protocol_compliance.py` and `enhanced_reflection.py`.
