# COMMANDS.md — Complete Workflow Catalog

> **Status**: Complete  
> **Last Updated**: 2026-02-16  
> **Total Workflows**: 12

This document catalogs all global agent workflows (slash commands), organized by use case category.

---

## Table of Contents

1. [Session Lifecycle](#session-lifecycle)
2. [Critical Thinking](#critical-thinking)
3. [Content/Reporting](#contentreporting)
4. [Evaluation](#evaluation)
5. [CI/CD](#cicd)
6. [Workflow Index](#workflow-index)

---

## Session Lifecycle

Workflows for managing agent sessions from start to finish.

### `/next`

**Purpose**: Determine what to work on next

**Description**: "What should we work on next?"

**Usage**: 
```
/next
```

**Expected Outcome**: Displays available Beads tasks with priority analysis and recommendations.

---

### `/wtu` (Wrap This Up)

**Purpose**: Properly close out the current session

**Description**: Run Phases 5-7 of the SOP to properly close out the session.

**Usage**:
```
/wtu
```

**Expected Outcome**: Executes Finalization (Phase 5), Retrospective (Phase 6), and Clean State (Phase 7) validations.

**Workflow Steps**:
1. Phase 5: Run quality gates, commit changes, sync with remote
2. Phase 6: Capture learnings and provide handoff summary
3. Phase 7: Verify repository is clean and ready for next session

---

### `/turbo-create`

**Purpose**: Fast administrative task workflow

**Description**: Use the Turbo Create protocol for administrative tasks that don't involve production code changes.

**Usage**:
```
/turbo-create
```

**Expected Outcome**: Quick initialization and finalization for issues, documentation, or meta-research.

**When to Use**:
- Issue management (`bd create`, `bd ready`)
- Minor documentation edits
- Meta-research and planning
- Any task NOT involving `.py`, `.js`, `.sh` source files

**Escalation**: If code changes are needed, stops and runs standard initialization with Implementation Plan.

---

## Critical Thinking

Workflows for challenging assumptions and improving plans.

### `/devils-advocate`

**Purpose**: Challenge ideas with counterarguments

**Description**: Use devil's advocate persona to point out flaws, counterarguments, missing evidence, and unintended consequences.

**Usage**:
```
/devils-advocate
```

**Expected Outcome**: Specific, actionable feedback identifying weaknesses in the current approach.

---

### `/devils-advocate-plan`

**Purpose**: Simplify plans through critical analysis

**Description**: Use devil's advocate persona to analyze a plan and find ways to simplify it.

**Usage**:
```
/devils-advocate-plan
```

**Expected Outcome**: Recommendations for simplifying the plan, reducing complexity, and lowering cognitive load.

---

### `/red-team`

**Purpose**: Hunt for weaknesses deliberately

**Description**: Act as a red team reviewer to find and poke holes in ideas, exposing flaws and loopholes.

**Usage**:
```
/red-team
```

**Expected Outcome**: Aggressive analysis exposing weaknesses, gaps, and potential failure points.

---

### `/red-team-plan`

**Purpose**: Simplify plans via red team analysis

**Description**: Use red team persona to analyze a plan and find ways to simplify it.

**Usage**:
```
/red-team-plan
```

**Expected Outcome**: Specific suggestions for simplifying complex plans.

---

### `/simplify`

**Purpose**: Reduce plan complexity

**Description**: Evaluate plans with attention to simplicity, error prevention, and lower cognitive load. Apply agile principle: start with simplest implementation, add complexity only when value is clearly justified.

**Usage**:
```
/simplify
```

**Expected Outcome**: Simplified plan with value-driven complexity analysis.

---

## Content/Reporting

Workflows for generating documentation and reports.

### `/reflect`

**Purpose**: Capture session learnings

**Description**: Session reflection and learning capture. Analyze conversation for patterns, extract user preferences, identify successful approaches and anti-patterns.

**Usage**:
```
/reflect
```

**Expected Outcome**: 
1. Analyze conversation for patterns and corrections
2. Extract user preferences and feedback
3. Identify successful approaches and anti-patterns
4. Update skill documentation with learnings
5. Apply improvements to prevent repeated mistakes

---

### `/writeup`

**Purpose**: Document feature reports

**Description**: Write up a summary of the speed/performance tradeoffs for a new feature and save it to the documentation.

**Usage**:
```
/writeup
```

**Expected Outcome**: Performance tradeoffs documented and reachable from the global index.

---

## Evaluation

Workflows for analyzing project integration decisions.

### `/evaluate`

**Purpose**: Analyze project integration proposals

**Description**: Critically evaluate the pros and cons of integrating `$ARGUMENT` into the project. Determine if it provides new capabilities or replicates existing ones.

**Usage**:
```
/evaluate <something-to-evaluate>
```

**Expected Outcome**: Analysis covering:
- New capabilities provided
- Duplication with existing features
- Integration complexity
- Trade-offs and risks

**Example**:
```
/evaluate GraphQL API
```

---

## CI/CD

Workflows for continuous integration and deployment.

### `/cicd`

**Purpose**: Fix CI/CD pipeline issues

**Description**: Fix issues with the CI/CD pipeline.

**Usage**:
```
/cicd <issue-description>
```

**Expected Outcome**: Identified CI/CD problems resolved with appropriate fixes.

---

## Workflow Index

| Command | Category | Purpose |
|:--------|:---------|:--------|
| `/cicd` | CI/CD | Fix CI/CD pipeline issues |
| `/devils-advocate` | Critical Thinking | Challenge ideas with counterarguments |
| `/devils-advocate-plan` | Critical Thinking | Simplify plans via devil's advocate |
| `/evaluate` | Evaluation | Analyze project integration proposals |
| `/next` | Session Lifecycle | Determine what to work on next |
| `/red-team` | Critical Thinking | Hunt for weaknesses deliberately |
| `/red-team-plan` | Critical Thinking | Simplify plans via red team |
| `/reflect` | Content/Reporting | Capture session learnings |
| `/simplify` | Critical Thinking | Reduce plan complexity |
| `/turbo-create` | Session Lifecycle | Fast administrative tasks |
| `/writeup` | Content/Reporting | Document feature reports |
| `/wtu` | Session Lifecycle | Wrap up session properly |

---

## Category Summary

| Category | Count | Commands |
|:---------|:-----:|:---------|
| Session Lifecycle | 3 | `/next`, `/wtu`, `/turbo-create` |
| Critical Thinking | 5 | `/devils-advocate`, `/devils-advocate-plan`, `/red-team`, `/red-team-plan`, `/simplify` |
| Content/Reporting | 2 | `/reflect`, `/writeup` |
| Evaluation | 1 | `/evaluate` |
| CI/CD | 1 | `/cicd` |

---

## Provider Compatibility

| Workflow | Provider-Agnostic | Provider-Specific |
|:---------|:------------------|:------------------|
| `/next` | ✅ Yes | - |
| `/wtu` | ✅ Yes | - |
| `/turbo-create` | ✅ Yes | - |
| `/devils-advocate` | ✅ Yes | - |
| `/devils-advocate-plan` | ✅ Yes | - |
| `/red-team` | ✅ Yes | - |
| `/red-team-plan` | ✅ Yes | - |
| `/simplify` | ✅ Yes | - |
| `/reflect` | ✅ Yes | - |
| `/writeup` | ✅ Yes | - |
| `/evaluate` | ✅ Yes | - |
| `/cicd` | ✅ Yes | - |

**All 12 workflows are provider-agnostic** and work with any LLM provider (Gemini, Claude, OpenAI, etc.).

---

## Overlap Analysis

### Critical Thinking Group

| Workflow | Primary Use | Overlaps With |
|:---------|:------------|:--------------|
| `/devils-advocate` | Challenge any idea | `/red-team` (similar purpose) |
| `/red-team` | Hunt for weaknesses | `/devils-advocate` (similar purpose) |
| `/simplify` | Reduce complexity | `/devils-advocate-plan`, `/red-team-plan` (goal) |
| `/devils-advocate-plan` | Simplify plans | `/red-team-plan`, `/simplify` |
| `/red-team-plan` | Simplify plans | `/devils-advocate-plan`, `/simplify` |

**Recommendation**: These workflows serve similar purposes. Consider consolidating into a single `/critique` or `/analyze` command that can take modifiers (e.g., `/critique --simplify`, `/critique --hunt`).

### Session Lifecycle Group

| Workflow | Primary Use | Overlaps With |
|:---------|:------------|:--------------|
| `/wtu` | Full session wrap-up | - |
| `/turbo-create` | Fast admin tasks | - |
| `/next` | Task selection | - |

**Note**: These are distinct and don't overlap significantly.

---

## Audit Complete

- [x] All 12 workflows cataloged
- [x] Categorized by use case (5 categories)
- [x] Provider-agnostic analysis completed
- [x] Overlap analysis completed

---

*Generated as part of agent-44b.2 & agent-44b.6: Cross-Agent Documentation & Skills Organization*
