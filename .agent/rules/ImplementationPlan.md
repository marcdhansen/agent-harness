# 📋 Implementation Plan: agent-harness-qzo - Standardized PR Template

## Objective

Create a standardized GitHub Pull Request template to ensure consistency in agent-led PRs.

## Proposed Changes

1. Create `.github/PULL_REQUEST_TEMPLATE.md` with the following sections:
   - **Beads Issue Reference**: Link to the relevant issue.
   - **Summary of Changes**: High-level overview of what was done.
   - **Testing Performed**: Details on how the changes were verified.
   - **Files Modified**: List of key files changed.
   - **Session Context**: Brief context for the reviewer (e.g., session ID, specific challenges).

## Verification

1. Manually check the content of `.github/PULL_REQUEST_TEMPLATE.md`.
2. Run Orchestrator compliance check to see if it complains about missing template (later, once integrated).

## Blast Radius

- Very low. Only adds a static template file used by GitHub.
