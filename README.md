# Agent Harness

Standard Mission Protocol (SMP) Harness for AI Agent Orchestration.

A flexible, two-tier agent orchestration framework that supports both simple task execution and full mission lifecycle management.

## Features

- **Inner Harness**: Minimal Pi Mono-style agent loop with 4 core tools (read, write, edit, bash)
- **Outer Harness**: Full LangGraph-powered SMP workflow with compliance checks
- **Human-in-the-Loop**: Interrupt-based approval workflows
- **Persistence**: SQLite-backed state checkpointing for resumable missions
- **Extensibility**: Custom tool registration and pluggable agents

## Installation

```bash
pip install agent-harness
```

## Quick Start

### Simple Mode (Inner Harness)

For quick, single-task execution without orchestration overhead:

```python
from agent_harness import InnerHarness

harness = InnerHarness(llm_client=my_llm)
result = harness.run("Add a factorial function to utils.py")
```

### Full Mode (Outer Harness)

For mission-critical workflows with compliance and checkpointing:

```python
from agent_harness import run_harness

result = run_harness(
    mission_id="TASK-001",
    description="Implement factorial with tests",
    thread_id="session-xyz"
)
```

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                     OUTER HARNESS (LangGraph)                   │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐    │
│  │   PFC   │───▶│ Approval │───▶│   IFO   │───▶│   RTB    │    │
│  └─────────┘    └──────────┘    └────┬────┘    └──────────┘    │
│                                      │                          │
│                                      ▼                          │
│                          ┌───────────────────┐                  │
│                          │   INNER HARNESS   │◀── Simple Mode   │
│                          │  (Pi Mono Style)  │    Entry Point   │
│                          └───────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

## License

MIT
