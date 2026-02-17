# SKILLS.md — Complete Skill Catalog

> **Status**: Complete  
> **Last Updated**: 2026-02-16  
> **Total Skills**: 24

This document catalogs all available agent skills, organized by tier with maturity levels and provider compatibility.

---

## Table of Contents

1. [Core Tier](#core-tier--p0-critical)
2. [Development Tier](#development-tier)
3. [Review Tier](#review-tier)
4. [System Tier](#system-tier)
5. [Specialized Tier](#specialized-tier)
6. [Skill Index](#skill-index)

---

## Core Tier — P0 Critical

Critical infrastructure skills required for SOP compliance and session management.

| Skill | Description | Maturity | Provider | Dependencies |
|:------|:------------|:---------|:---------|:-------------|
| **Orchestrator** | Verifies SOP compliance at each phase (Initialization, Finalization). Validates agents complete steps and invoke skills appropriately. | 🟢 Stable | All | None |
| **tdd** | Test-Driven Development best practices. Enforces test-first development for all code changes. | 🟢 Stable | All | None |
| **planning** | Blast radius analysis, incremental validation, value-driven change management. | 🟢 Stable | All | show-next-task, finalization, reflect |
| **finalization** | Performs Finalization checks: git status, quality gates, issue updates, session closure. | 🟢 Stable | All | None |
| **reflect** | Analyzes conversation to extract lessons, updates SKILL.md files. Enhanced version includes protocol integration. | 🟢 Stable | All | None |
| **retrospective** | Post-session strategic analysis. Synthesizes results, reflection learnings, generates improvement suggestions. | 🟢 Stable | All | None |

---

## Development Tier

Skills supporting code implementation, debugging, and navigation.

| Skill | Description | Maturity | Provider | Dependencies |
|:------|:------------|:---------|:---------|:-------------|
| **git** | Comprehensive Git workflow: commits, branches, merges, rebases, conflict resolution. | 🟢 Stable | All | None |
| **debugging** | Systematic debugging: reproduction, isolation, tools, patterns. | 🟢 Stable | All | None |
| **code-navigation** | Efficient codebase navigation: find functions/classes, dependencies, project structure. | 🟢 Stable | All | None |
| **code-review** | Checklist-based review: logic errors, test coverage, PR size validation. | 🟢 Stable | All | None |
| **testing** | Test execution, data management, benchmark coordination. | 🟢 Stable | All | None |
| **ui** | WebUI development, deployment, testing, UX optimization. | 🟡 Evolving | All | None |
| **tdd-beads** | Automatic beads issue creation with TDD compliance enforcement. | 🟢 Stable | All | planning, finalization, reflect |

---

## Review Tier

Quality assurance and validation skills.

| Skill | Description | Maturity | Provider | Dependencies |
|:------|:------------|:---------|:---------|:-------------|
| **devils-advocate** | Critical thinking: challenges assumptions, generates counterarguments, demands evidence. | 🟢 Stable | All | None |
| **sop-modification** | Best practices for SOP enforcement. TDD required when modifying mandatory gates. | 🟢 Stable | All | tdd |

---

## System Tier

Project operations and orchestration skills.

| Skill | Description | Maturity | Provider | Dependencies |
|:------|:------------|:---------|:---------|:-------------|
| **process** | CI/CD pipelines, release procedures, quality gates. | 🟡 Evolving | All | None |
| **multi-model-orchestrator** | Orchestrates specialized agents across different LLM models (Sisyphus, Hephaestus, Oracle, Librarian). | 🔴 Experimental | OpenAI | None |
| **openviking** | Enhanced agent system with improved skill discovery and memory management. | 🔴 Experimental | OpenAI | None |

---

## Specialized Tier

Niche skills for specific use cases.

| Skill | Description | Maturity | Provider | Dependencies |
|:------|:------------|:---------|:---------|:-------------|
| **browser-manager** | Playwright browser lifecycle: tab tracking, soft warnings, cross-agent cleanup. | 🟢 Stable | All | None |
| **notebooklm** | Query Google NotebookLM notebooks with Gemini source-grounded answers. | 🟢 Stable | Gemini | None |
| **skill-making** | Guidelines for creating robust skills that work in interactive and non-interactive environments. | 🟢 Stable | All | None |
| **initialization-briefing** | Pre-session briefing: current status, protocol highlights, friction areas. | 🟢 Stable | All | None |
| **show-next-task** | Shows next task via beads ready with intelligent recommendations. | 🟢 Stable | All | None |
| **context-management** | Context window optimization for long sessions: compression, summarization. | 🟢 Stable | All | None |

---

## Maturity Levels

| Level | Symbol | Meaning |
|:------|:-------|:--------|
| Stable | 🟢 | Production-ready, well-tested |
| Evolving | 🟡 | Functional but may change |
| Experimental | 🔴 | Prototype, unstable API |

---

## Provider Compatibility

| Provider | Compatible Skills |
|:---------|:------------------|
| All | Orchestrator, tdd, planning, finalization, reflect, retrospective, git, debugging, code-navigation, code-review, testing, ui, tdd-beads, devils-advocate, sop-modification, process, browser-manager, skill-making, initialization-briefing, show-next-task, context-management |
| OpenAI | multi-model-orchestrator, openviking |
| Gemini | notebooklm |

---

## Dependency Graph

```
planning ─────┬──> finalization ──> retrospective
              │         │
tdd-beads ────┤         └──> reflect
              │
              └──> show-next-task

sop-modification ──> tdd
```

---

## Skill Index

| Skill | Tier | Invocation |
|:------|:-----|:-----------|
| browser-manager | Specialized | Manual |
| code-navigation | Development | Manual |
| code-review | Development | Manual |
| context-management | Specialized | Manual |
| debugging | Development | Manual |
| devils-advocate | Review | Manual |
| finalization | Core | /finalization |
| git | Development | Manual |
| initialization-briefing | Specialized | /initialization-briefing |
| multi-model-orchestrator | System | Manual |
| notebooklm | Specialized | Manual |
| openviking | System | Manual |
| Orchestrator | Core | Auto (session start) |
| planning | Core | /plan |
| process | System | Manual |
| reflect | Core | /reflect |
| retrospective | Core | /retrospective |
| show-next-task | Specialized | /show-next-task |
| skill-making | Specialized | /skill-making |
| sop-modification | Review | Manual |
| tdd | Core | /tdd |
| tdd-beads | Development | /tdd-beads |
| testing | Development | Manual |
| ui | Development | Manual |

---

## Usage Notes

1. **Core skills** are automatically invoked by the Orchestrator at appropriate phases
2. **Development skills** should be invoked manually when working on code
3. **Review skills** support quality assurance workflows
4. **System skills** manage project infrastructure
5. **Specialized skills** address specific niche requirements

---

## Audit Findings

### Completeness Check

| Check | Status |
|:------|:-------|
| All skills have SKILL.md | ✅ 24/24 |
| Proper frontmatter | ✅ 24/24 |
| Outdated references (Flight Director) | ✅ None found |

### Overlap Analysis

| Skills | Overlap | Recommendation |
|:-------|:--------|:--------------|
| testing vs tdd | Some overlap - both involve testing | Keep separate - testing is for test execution, tdd is for test-first methodology |
| process vs planning | No overlap | Keep separate - process is CI/CD, planning is feature planning |
| multi-model-orchestrator vs Orchestrator | No overlap | Keep separate - multi-model is for LLM routing, Orchestrator is for SOP compliance |

### Key Observations

- **testing**: Manages test execution, data, and benchmarks (LightRAG-specific)
- **tdd**: Enforces test-first methodology (general practice)
- **process**: CI/CD pipelines and release procedures
- **planning**: Feature scoping and blast radius analysis
- **multi-model-orchestrator**: Routes tasks to specialized LLM agents
- **Orchestrator**: Validates SOP compliance

---

*Generated as part of agent-44b.1 & agent-44b.7: Cross-Agent Documentation & Skills Organization*
