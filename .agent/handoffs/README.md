# Handoffs Directory

This directory stores session handoff documents for task continuity.

## Structure

- `{issue-id}.md` - Handoff document for a specific issue

## Usage

Handoffs should be created during session finalization to pass context to the next agent or session.

## Cleanup

**IMPORTANT**: Handoff files are automatically deleted when the associated beads issue is closed after PR merge.

This cleanup happens during finalization to keep the directory lean.

## Example

```
.agent/handoffs/agent-53u.md
```

See the Planning Skill documentation for template usage.
