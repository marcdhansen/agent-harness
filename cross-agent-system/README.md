# Cross-Agent System — Master Index

> **Status**: Complete  
> **Last Updated**: 2026-02-16

The **Cross-Agent System** is a comprehensive framework for orchestrating multiple AI agents across complex tasks. This directory contains the complete documentation, workflows, and implementation guides.

---

## Quick Links

| Resource | Description |
|:---------|:------------|
| [SKILLS.md](./SKILLS.md) | Complete catalog of 24 agent skills |
| [COMMANDS.md](./COMMANDS.md) | Complete catalog of 12 workflow commands |

---

## Documentation Overview

### Core Documentation

| Document | Description |
|:---------|:------------|
| `universal-agent-system-roadmap.md` | Long-term vision and roadmap for the agent system |
| `sandboxed-agents-strategy.md` | Strategy for running agents in isolated environments |
| `vfs-implementation-guide.md` | Virtual filesystem implementation for agent coordination |
| `api-service-reference-implementation.md` | API service reference architecture |

### Planning & Execution

| Document | Description |
|:---------|:------------|
| `Epic Plan Execution - Quick Reference Card.md` | Quick reference for epic execution |
| `Revised Epic Plan - Validation & Execution Guide.md` | Detailed validation and execution guidance |
| `Epic Plan Feedback - Detailed Improvements.md` | Feedback and improvement recommendations |
| `Strategic Decision Framework - MUST RESOLVE FIRST.md` | Critical strategic decisions |

### Implementation Guides

| Document | Description |
|:---------|:------------|
| `quick-wins-guide.md` | Low-effort, high-impact improvements |
| `decisions/` | Architecture Decision Records (ADRs) |

---

## Getting Started

### For New Agents

1. **Read SKILLS.md** — Understand available capabilities
2. **Read COMMANDS.md** — Learn workflow commands
3. **Review this index** — Find relevant documentation

### Common Workflows

| Task | Command | Documentation |
|:-----|:--------|:--------------|
| What to work on next? | `/next` | [COMMANDS.md](./COMMANDS.md#next) |
| Start a session | Standard SOP | [AGENTS.md](../AGENTS.md) |
| End a session | `/wtu` | [COMMANDS.md](./COMMANDS.md#wtu-wrap-this-up) |
| Reflect on session | `/reflect` | [COMMANDS.md](./COMMANDS.md#reflect) |
| Evaluate integration | `/evaluate` | [COMMANDS.md](./COMMANDS.md#evaluate) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Harness                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Sisyphus  │  │  Hephaestus│  │   Oracle    │      │
│  │   (Lead)   │  │   (Forge)  │  │ (Validator) │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
├─────────────────────────────────────────────────────────┤
│                    Skills (24)                          │
│  Orchestrator | TDD | Planning | Finalization | ...    │
├─────────────────────────────────────────────────────────┤
│                  Workflows (12)                         │
│  /next | /wtu | /reflect | /evaluate | ...             │
└─────────────────────────────────────────────────────────┘
```

---

## Skills Overview

| Tier | Count | Examples |
|:-----|:-----:|:---------|
| Core (P0) | 6 | Orchestrator, TDD, Planning |
| Development | 7 | Git, Debugging, Code Review |
| Review | 2 | Devil's Advocate, SOP Modification |
| System | 3 | Process, Multi-Model Orchestrator |
| Specialized | 6 | Browser Manager, NotebookLM |

**See**: [SKILLS.md](./SKILLS.md)

---

## Commands Overview

| Category | Count | Commands |
|:---------|:-----:|:---------|
| Session Lifecycle | 3 | `/next`, `/wtu`, `/turbo-create` |
| Critical Thinking | 5 | `/devils-advocate`, `/red-team`, `/simplify` |
| Content/Reporting | 2 | `/reflect`, `/writeup` |
| Evaluation | 1 | `/evaluate` |
| CI/CD | 1 | `/cicd` |

**See**: [COMMANDS.md](./COMMANDS.md)

---

## Directory Structure

```
cross-agent-system/
├── SKILLS.md                           # Skill catalog
├── COMMANDS.md                         # Workflow commands
├── README.md                           # This file
├── universal-agent-system-roadmap.md   # Long-term roadmap
├── sandboxed-agents-strategy.md        # Isolation strategy
├── vfs-implementation-guide.md        # VFS implementation
├── api-service-reference-implementation.md
├── quick-wins-guide.md                # Quick wins
├── Epic Plan Execution - Quick Reference Card.md
├── Epic Plan Feedback - Detailed Improvements.md
├── Revised Epic Plan - Validation & Execution Guide.md
├── Strategic Decision Framework - MUST RESOLVE FIRST.md
└── decisions/                         # ADRs
    └── ADR-*.md
```

---

## Related Resources

- **Main Project**: [../README.md](../README.md)
- **SOP Documentation**: [../AGENTS.md](../AGENTS.md)
- **Implementation Plan**: [../ImplementationPlan.md](../ImplementationPlan.md)
- **Skills Repository**: `~/.config/opencode/skills/`
- **Workflows Repository**: `~/.gemini/antigravity/global_workflows/`

---

*Generated as part of agent-44b.3: Cross-Agent Documentation & Skills Organization*
