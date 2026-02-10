# Task: agent-harness-6qg - Convert SOP checklists to JSON format

## Problem

Currently, SOP checklists are defined in Markdown (`SOP_COMPLIANCE_CHECKLIST.md`). While human-readable, they are difficult for agents to programmatically validate and update consistently. The Orchestrator has hardcoded logic that mirrors these checklists, leading to duplication and maintenance overhead.

## Objective

Convert the SOP checklists into a structured JSON format to enable programmatic validation, dynamic reporting, and reduced coupling between the Orchestrator and the documentation.

## Proposed Changes

1. **Define JSON Schema**: Create `.agent/rules/sop_checklist.schema.json` to define the structure of a phase-based checklist.
2. **Generate JSON Checklists**: Create `.agent/rules/checklists/` directory and populate it with JSON files for each SOP phase (Initialization, Planning, Execution, Finalization, Retrospective, Clean State).
3. **Update Orchestrator**: Modify `check_protocol_compliance.py` to:
    - Load checklists from JSON.
    - Map JSON check IDs to Python validator functions.
    - Report status based on the JSON-defined checks.
4. **Maintain Documentation**: Ensure `SOP_COMPLIANCE_CHECKLIST.md` remains the human-readable view, possibly by generating it from the JSON or vice-versa (for this task, we will focus on JSON as the source of truth).

## Success Criteria

- [ ] JSON Schema defines phase, description, status (MANDATORY/OPTIONAL), and check details.
- [ ] All phases from `SOP_COMPLIANCE_CHECKLIST.md` are represented in JSON.
- [ ] Orchestrator runs all checks defined in JSON.
- [ ] Orchestrator output matches the JSON-defined structure.
- [ ] tests/test_sop_json_validation.py passes.

## Progress

- [x] Initial research on SOP and Orchestrator.
- [x] Task initialized and branch created.
- [x] Define JSON Schema.
- [x] Convert MD checklists to JSON.
- [x] Update Orchestrator logic.
- [ ] Verify compliance.

## Approval

- [x] APPROVED FOR EXECUTION

## Friction Log

- None yet.
