# Task: agent-harness-2rn - Standardize structured JSON for reflection capture

## Objective

Make `.reflection_input.json` the standard reflection artifact to enable machine-readable validation, consistent formatting, and automated pattern analysis across sessions.

## Roadmap

- [x] **Phase 1: Planning & Initialization**
  - [x] Claim task `agent-harness-2rn`
  - [x] Create feature branch `agent/agent-harness-2rn`
  - [x] Establish implementation plan
  - [x] Get plan approval
- [x] **Phase 2: Schema Definition & Tooling**
  - [x] Define the official JSON schema for `.reflection_input.json`
  - [x] Create a utility script to validate reflection JSON against the schema (Integrated into Orchestrator)
- [x] **Phase 3: Skill & Orchestrator Enhancement**
  - [x] Update `/reflect` skill to output structured JSON
  - [x] Update `check_protocol_compliance.py` to enforce the existence and validity of `.reflection_input.json` during `--retrospective`
- [x] **Phase 4: Testing & Verification**
  - [x] Create tests for reflection validation
  - [x] Verify Orchestrator blocks finalization if reflection JSON is missing or invalid
- [x] **Phase 5: Finalization**
  - [x] Update SOP documentation to reflect the new requirement
  - [x] Submit PRs for `agent-harness`, `dot-gemini`, and potentially `dot-agent`
  - [x] Complete session and hand off

## Plan Status

- [x] Implementation Complete
