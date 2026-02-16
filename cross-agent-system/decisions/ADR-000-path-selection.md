# ADR-000: Strategic Path Selection — Hybrid/Staged (Path C)

**Status**: Accepted  
**Date**: 2026-02-16  
**Decision Makers**: Marc Hansen  
**Context**: Cross-Agent System Documentation, Slash Commands & Skills Organization

---

## Decision

**Chosen Path: C — Hybrid/Staged**

Get documentation accurate first (proves value immediately), implement quick-wins next (low risk, high impact), then decide on larger architectural changes (VFS, API service, sandboxed agents) with real usage data.

## Context

The cross-agent-system directory contains 5 documents (~4,800 lines) spanning current-state documentation and aspirational enterprise architecture. Three paths were evaluated:

| Path | Scope | Effort | Risk |
|---|---|---|---|
| A: Accuracy-Only | Document what exists, mark roadmap as "future" | ~24 hrs | Low |
| **C: Hybrid/Staged** ⭐ | Docs first → quick-wins → decide with data | ~42 hrs (Phase 1) | Low–Medium |
| B: Full Transformation | Implement VFS, provider abstraction, API service | ~200 hrs | High |

## Rationale

1. **Immediate value**: Accurate documentation for 24 skills and 12 workflows is needed regardless of path
2. **Deferred risk**: VFS/API/sandboxing decisions carry ~200 hours of effort and shouldn't be committed to without proving the quick-wins first
3. **Optionality**: Path C preserves the ability to escalate to Path B later, or stop at Path A if docs prove sufficient
4. **Data-driven**: Quick-wins implementation will generate real usage data to inform larger architecture decisions

## Consequences

### What We Will Do

- **Phase 1 (now)**: 4 epics, 17 issues, ~42 hours — full documentation audit, organization, and strategic review
- **Phase 2 (after Phase 1)**: Implement quick-wins (provider auto-detection, structured logging, health checks) — ~30–40 additional hours
- **Phase 3 (after Phase 2)**: Decide on VFS/API/sandboxing with usage data — ADR-001 through ADR-004

### What We Will Not Do (Yet)

- Implement the Virtual File System
- Build the API service
- Implement sandboxed agent strategies
- Build a skills package manager or registry

### Risks Accepted

- Quick-wins may become obsolete if we later choose Path B (low probability — quick-wins are useful regardless)
- Documentation may need updates after Phase 2 implementation (acceptable overhead)

## Related Documents

- [Implementation Plan](file:///Users/marchansen/.gemini/antigravity/brain/01947649-415f-43af-a6ce-08c20f8c3f16/implementation_plan.md)
- [Universal Agent System Roadmap](file:///Users/marchansen/lightrag/agent-harness/cross-agent-system/universal-agent-system-roadmap.md)
- [Quick Wins Guide](file:///Users/marchansen/lightrag/agent-harness/cross-agent-system/quick-wins-guide.md)
