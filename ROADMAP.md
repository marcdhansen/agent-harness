# Agent Harness Master Roadmap

This roadmap consolidates the "Solo Developer Roadmap" recommendations with the original SOTA Roadmap Epics. It provides a structured, phased approach to building a state-of-the-art agent harness.

## 🏗️ Architecture

The core architectural approach is to build governance and security layers incrementally. The original goal of **Simplifying Architecture (#9)**—specifically the consolidation of inner/outer harness complexities—is addressed implicitly through this phased build-up. By starting with robust trajectory logging (Phase 0) and isolated sandboxing (Phase 1), we ensure a clean separation of concerns without a bloated initial architecture.

---

## 📅 Phase 0: Foundation (Weeks 1-2)

**Goal**: Complete audit trail and baseline data quality.

### Trajectory Logging

- **What**: Build a comprehensive JSONL logging system for all agent actions, observations, and decisions.
- **Related prior epic**: #6 (06-trajectory-logging.md)
- **Status**: Ready for execution

### Data Babysitting (Standalone)

- **What**: Build an independent data quality monitoring and auto-repair library.
- **Related prior epic**: None (New concept)

---

## 📅 Phase 1: Guardian & Infrastructure (Weeks 3-6)

**Goal**: Autonomous oversight and secure isolation.

### Guardian Agents

- **What**: Build a risk assessment and approval system to intercept and monitor agent actions.
- **Related prior epic**: None (Extends philosophy of #2)

### Sandboxing & Permissions

- **What**: Implement Colima/Docker container isolation and a robust permission manager.
- **Related prior epic**: #2 (02-sandboxing-permission-system.md)
- **Note**: Architecturally independent of Guardian Agents; serves as the security enforcement layer.

### Multi-Provider

- **What**: Abstract provider interface with Model Context Protocol (MCP) support.
- **Related prior epic**: #1 (01-multi-llm-provider-support.md)

### Observability

- **What**: Set up OpenTelemetry, Prometheus, and Grafana for real-time monitoring.
- **Related prior epic**: #10 (10-performance-metrics.md)

---

## 📅 Phase 2: Intelligence & Memory (Weeks 7-10)

**Goal**: Temporal memory and workflow orchestration.

### TG-RAG Memory

- **What**: Bi-level temporal graph architecture for efficient long-term fact retrieval.
- **Related prior epic**: #5 (05-context-window-management.md)
- **Integration**: **GreedyPack** strategy will be integrated into the Context Manager.

### Context Window Management

- **What**: Handle live session token limits through eviction, compression, and summarization.
- **Related prior epic**: #5 (05-context-window-management.md)
- **Relationship**: Complements TG-RAG; handles short-term context while TG-RAG handles long-term retrieval.

### LangGraph

- **What**: Multi-step workflow orchestration using cyclic graphs and state management.
- **Related prior epic**: None (New concept)

---

## 📅 Phase 3: Governance & Quality (Weeks 11-13)

**Goal**: Production-ready oversight and resilience.

### Governance Board

- **What**: Digital workforce monitoring, ethical alignment, and compliance reporting.
- **Related prior epic**: #6 (06-trajectory-logging.md) foundation.

### Behavior Testing

- **What**: Automated regression testing for agent behaviors and safety refusals.
- **Related prior epic**: None (New concept)

### Self-Healing

- **What**: Resilience patterns including circuit breakers, retries, and proactive fallbacks.
- **Related prior epic**: None (New concept)

---

## 🚀 Future Roadmap

The following items are deferred for post-Phase 3 development or when multiple agents/complex tools are required.

- **Git Worktree Integration**: Isolated workspaces for parallel agents. (#8)
- **Enhanced Coding Tools**: Advanced tools for code analysis and modification. (#4)
- **Concurrent Execution**: Managing multiple agents simultaneously. (#7 - Requires **#2 Sandboxing** and #8 Git Worktree as prerequisites)
- **Debugging Capabilities**: Interactive debugging, state inspection, and time-travel replay. (#3)
