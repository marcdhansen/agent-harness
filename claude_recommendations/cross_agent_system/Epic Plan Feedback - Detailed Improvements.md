# Epic Plan Feedback - Detailed Improvements

**Date**: February 16, 2026  
**Context**: Feedback on 5-epic, 18-issue documentation improvement plan

---

## ✅ What's Working Well

### Epic 1: Documentation Accuracy
**Strong points**:
- ✅ Foundation-first approach is correct
- ✅ Skills catalog (Issue 1.1) is critical - 5/24 documented is unacceptable
- ✅ Commands catalog (Issue 1.2) is equally critical - 3/12 documented is too low
- ✅ Priority P1 for both is appropriate

**Suggestions**:
1. **Add Issue 1.5: Create Documentation Health Dashboard**
   - Script that validates all docs are current
   - Runs on commit/push to detect drift
   - Example: `~/.agent/scripts/validate-docs.py`
   - Prevents docs from drifting again

2. **Expand Issue 1.1 scope**:
   - Not just "document" skills, but **standardize format**
   - All SKILL.md files should have identical structure
   - Add template: `~/.agent/templates/SKILL.md.template`
   - Enforce in pre-commit hook

3. **Issue 1.2 needs categorization**:
   - Current plan says "categorize" but doesn't define categories
   - Suggest:
     - **Session Management**: wtu (wrap this up), next
     - **Code Quality**: reflect, devils-advocate, red-team, simplify
     - **Planning Variants**: devils-advocate-plan, red-team-plan
     - **Content Creation**: writeup, turbo-create, evaluate
     - **CI/CD**: cicd
   - Add to each workflow: `category: session-management`

---

### Epic 2: Cross-Agent System Document Organization

**Strong points**:
- ✅ Master index (Issue 2.1) is essential for navigation
- ✅ Maturity headers (Issue 2.2) prevent confusion about aspirational vs real

**Problems**:
1. **Issue 2.4 (Reconcile Quick-Wins) is strategic, not organizational**
   - This assumes you're implementing the roadmap
   - Should be in Epic 5, not Epic 2
   - Or needs the strategic decision framework I created

2. **Missing: Deprecation Strategy**
   - What if roadmap docs contradict current architecture?
   - Need decision: keep both? deprecate one? merge?
   - Add Issue 2.5: "Resolve Documentation Conflicts"

3. **Issue 2.1 (Master Index) scope too narrow**
   - Should also link to **implementation locations**
   - E.g., "VFS Implementation → See `~/.agent/core/vfs.py` (not yet implemented)"
   - Add "Implementation Status" column to index

**Revised Issue 2.1**:
```markdown
## Issue 2.1: Create Cross-Agent System Master Index

Create `cross-agent-system/README.md` with:

### Document Map
| Document | Status | Implementation | Depends On |
|----------|--------|----------------|------------|
| universal-agent-system-roadmap.md | Draft | Not Started | - |
| quick-wins-guide.md | Ready | Partial (see below) | Roadmap |
| vfs-implementation-guide.md | Draft | Not Started | Quick-wins |
| sandboxed-agents-strategy.md | Draft | Not Started | VFS |
| api-service-reference-implementation.md | Draft | Not Started | VFS, Sandboxed |

### Quick-Wins Implementation Status
- [ ] Provider auto-detection → `~/.agent/core/provider_detection.py` (not started)
- [ ] Structured logging → `~/.agent/core/logging.py` (not started)
- [ ] Health checks → `~/.agent/core/health.py` (not started)
- [ ] Session state → `~/.agent/core/session_state.py` (not started)

### Reading Order
1. **Start here if new**: AGENTS.md → GLOBAL_INDEX.md → this README
2. **For immediate improvements**: quick-wins-guide.md
3. **For full transformation**: roadmap → VFS → sandboxed → API
4. **For integration patterns**: existing-systems-analysis.md → practical-integration-guide.md

### Architecture Decision Records
See `cross-agent-system/decisions/` for:
- ADR-001: VFS vs Symlinks
- ADR-002: API Service Deployment Strategy
- ADR-003: Provider Abstraction Approach
```

---

### Epic 3: Slash Commands & Workflows Rationalization

**Strong points**:
- ✅ Audit & categorize (Issue 3.1) is correct first step
- ✅ Identified 12 workflows is accurate

**Problems**:
1. **Issue 3.1 categories are too abstract**
   - "Session Lifecycle" - what does this mean to a user?
   - "Analysis & Review" - how do I choose between them?
   - Need **use-case based categories**:
     - "Starting/Ending Work": wtu, next
     - "Improving Code Quality": reflect, simplify, devils-advocate, red-team
     - "Creating Deliverables": writeup, turbo-create
     - "Validating Approaches": evaluate, devils-advocate-plan, red-team-plan
     - "Automation": cicd

2. **Issue 3.2 is premature**
   - Can't create project-level workflows until you understand global ones
   - Should be P4 (backlog), not P3
   - Or remove entirely - project workflows should emerge from need

3. **Missing: Usage Analytics**
   - Which workflows are actually used?
   - Which are obsolete?
   - Add Issue 3.4: "Analyze Workflow Usage Patterns"
   - Check git history, logs, mentions in progress-logs/

**New Issue 3.4: Analyze Workflow Usage**:
```bash
# Script to analyze workflow usage
for workflow in ~/.gemini/antigravity/global_workflows/*.md; do
  name=$(basename "$workflow" .md)
  mentions=$(grep -r "/$name" ~/.agent/progress-logs/ 2>/dev/null | wc -l)
  git_history=$(git log --all --oneline -- "$workflow" | wc -l)
  echo "$name: $mentions mentions, $git_history commits"
done | sort -t: -k2 -nr
```

**Revised Issue 3.1 with categories**:
```markdown
## Issue 3.1: Audit & Categorize All Global Workflows

### Proposed Categories (Use-Case Based)
1. **Session Management** (when starting/ending work)
   - `/wtu` - Wrap this up (finalization)
   - `/next` - What to do next
   - Status: Essential, widely used

2. **Code Review & Quality** (before committing)
   - `/reflect` - Reflect on session learnings
   - `/simplify` - Simplify complex code
   - `/devils-advocate` - Critical review
   - `/red-team` - Security/robustness review
   - Status: Quality gates, important

3. **Planning Validation** (before implementing)
   - `/devils-advocate-plan` - Challenge the plan
   - `/red-team-plan` - Attack the plan
   - Status: Risk reduction, recommended

4. **Content Generation** (creating artifacts)
   - `/writeup` - Generate documentation
   - `/turbo-create` - Quick content creation
   - Status: Productivity tools

5. **Analysis** (understanding/validating)
   - `/evaluate` - Evaluate approach/code
   - Status: Decision support

6. **Automation** (CI/CD integration)
   - `/cicd` - CI/CD workflows
   - Status: Infrastructure

### Overlaps to Resolve
- `/devils-advocate` vs `/red-team` - Are both needed? If yes, when to use which?
- `/devils-advocate-plan` vs `/red-team-plan` - Same question
- `/reflect` vs `/evaluate` - Scope overlap?

### Provider Compatibility
Mark each workflow:
- 🌍 Universal (works with any provider)
- 🔷 Gemini-specific
- 🟣 Claude-specific
- ⚠️ Needs testing
```

---

### Epic 4: Skills Organization & Governance

**Strong points**:
- ✅ Audit all 24 skills (Issue 4.1) is necessary
- ✅ Dependency map (Issue 4.2) is insightful
- ✅ Overlap resolution (Issue 4.3) is important

**Problems**:
1. **Epics 3 & 4 are too similar**
   - Both are "catalog and categorize exercises"
   - Both have overlaps to resolve
   - Consider merging into **Epic 3: Catalog & Rationalize Resources**
   - Sub-epics: 3A (Workflows), 3B (Skills)

2. **Issue 4.3 needs decision criteria**
   - How do you decide merge vs deprecate vs clarify?
   - Add criteria:
     - **Merge if**: >80% functional overlap, different names for same thing
     - **Deprecate if**: Not used in 6 months, superseded by better alternative
     - **Clarify if**: Different purposes but similar names/descriptions
   - Add to issue description

3. **Issue 4.1 should produce artifact**
   - Not just "verify" but create **Skills Health Report**
   - Format:
     ```
     Skills Audit Report - Feb 16, 2026
     ================================
     Total Skills: 24
     
     Health Status:
     ✅ Complete: 18 (75%)
     ⚠️  Incomplete: 4 (17%)
     ❌ Broken: 2 (8%)
     
     By Category:
     - Core: 6 skills (all healthy)
     - Development: 8 skills (2 incomplete)
     - Review: 5 skills (all healthy)
     - Specialized: 5 skills (2 broken)
     
     Action Required:
     - Fix: testing/ (missing scripts/)
     - Fix: skill-making/ (outdated references)
     - Complete: custom-instructions/ (missing SKILL.md)
     - Complete: multi-model-orchestrator/ (missing examples/)
     ```

**Revised Issue 4.3 with criteria**:
```markdown
## Issue 4.3: Identify and Resolve Skill Overlaps

### Decision Criteria
For each potential overlap, evaluate:

**Merge** if:
- Functional overlap > 80%
- Different names for essentially same capability
- One is clearly better implementation
- Example: If `testing/` and `tdd/` do the same thing, keep best one

**Deprecate** if:
- Not used in last 6 months (check git history)
- Superseded by newer, better alternative
- References obsolete concepts (e.g., old "Flight Director")
- Mark as deprecated, plan removal after 1 quarter

**Clarify** if:
- Legitimate different purposes
- Confusing names but distinct functionality
- Rename or document clear boundaries
- Example: `process/` vs `planning/` might be different scopes

### Specific Investigations

#### 1. testing/ vs tdd/
**Overlap assessment**: [TBD]
**Recommendation**: [Merge / Deprecate / Clarify]
**Rationale**: [explain]

#### 2. process/ vs planning/
**Overlap assessment**: [TBD]
**Recommendation**: [Merge / Deprecate / Clarify]
**Rationale**: [explain]

#### 3. skill-making/ 
**Usage analysis**: [TBD - check git history]
**Recommendation**: [Keep / Deprecate]
**Rationale**: [explain]

#### 4. multi-model-orchestrator/ vs Orchestrator/
**Relationship**: [Are these related? Different? Redundant?]
**Recommendation**: [TBD]
**Rationale**: [explain]

### Implementation
For each decision:
1. Document in `SKILLS.md`
2. If deprecating: Add deprecation notice to SKILL.md
3. If merging: Create migration guide
4. If clarifying: Update descriptions in both skills
```

---

### Epic 5: Roadmap-to-Implementation Pipeline

**Major Problem**: This epic is **premature**

**Why**:
- You haven't decided IF you want to implement the roadmap
- Issue 5.1 (Triage to Beads) assumes you're doing it
- Issue 5.2 (Decision Log) is strategic, not implementation

**Recommendation**:
1. **Defer Epic 5 entirely** until after Epics 1-4 complete
2. Add **strategic decision gate** after Epic 4
3. Replace with **Epic 5: Strategic Review & Next Steps**:

```markdown
## Epic 5: Strategic Review & Next Steps
Goal: With complete, accurate documentation, decide future direction

### Issue 5.1: Team Review of Complete Documentation
Priority: P1 (gates all future work)
Effort: 2-4 hours (meeting + prep)

Present completed docs to team:
- SKILLS.md with all 24 skills
- COMMANDS.md with all 12 workflows
- Cross-agent-system/ with status markers
- Dependency maps and overlap resolutions

Questions to answer:
1. Is current system meeting our needs?
2. What problems are we actually experiencing?
3. Are sandboxed environments a real requirement?
4. Do we have resources for transformation?

### Issue 5.2: Architecture Decision Records
Priority: P1 (documents decisions)
Effort: 3-4 hours

Create `cross-agent-system/decisions/` with ADRs for:

**ADR-001: VFS vs Symlinks Decision**
- Context: Symlinks are OS-dependent, break on Windows
- Options: Keep symlinks / Implement VFS / Hybrid
- Decision: [TBD after review]
- Consequences: [effort, risk, benefits]

**ADR-002: API Service Strategy**
- Context: Sandboxed environments need remote access
- Options: Don't support sandboxed / Self-hosted API / SaaS API
- Decision: [TBD after review]
- Consequences: [cost, maintenance, capabilities]

**ADR-003: Implementation Path**
- Context: Have aspirational roadmap vs working system
- Options: Path A (docs only) / Path B (full roadmap) / Path C (staged)
- Decision: [TBD after review]
- Consequences: [timeline, resources, risk]

### Issue 5.3: Prioritized Implementation Backlog
Priority: P2 (only if implementing changes)
Effort: 2-3 hours

IF decision is to implement changes:
- Create Beads epic for chosen path
- Break down into 2-week sprints
- Assign priorities and owners
- Set milestones and checkpoints

IF decision is docs-only:
- Create maintenance plan for keeping docs current
- Set up doc validation automation
- Establish review cadence
```

---

## 🔄 Suggested Epic Structure Changes

### Option 1: Keep 5 Epics (Minor Changes)
```
Epic 1: Documentation Accuracy ✅ (keep as-is with Issue 1.5 added)
Epic 2: Cross-Agent Org ⚠️ (move Issue 2.4 to new Epic 5)
Epic 3: Workflows ⚠️ (add Issue 3.4, revise categories)
Epic 4: Skills ⚠️ (add decision criteria to Issue 4.3)
Epic 5: Strategic Review ⚠️ (replace entirely with review/decision)
```

### Option 2: Merge Similar Epics (Cleaner)
```
Epic 1: Foundation - Documentation Accuracy
  └─ Issues 1.1, 1.2, 1.3, 1.4, 1.5

Epic 2: Organization - Structure & Navigation
  └─ Issues 2.1, 2.2, 2.3

Epic 3: Resource Catalog - Workflows & Skills
  └─ Sub-Epic 3A: Workflows (Issues 3.1, 3.3, 3.4)
  └─ Sub-Epic 3B: Skills (Issues 4.1, 4.2, 4.3, 4.4)

Epic 4: Strategic Review & Decision
  └─ Issues 5.1, 5.2, 5.3
  └─ Gates: Implement changes OR maintain only
```

**Recommendation**: Option 2 - cleaner separation of concerns

---

## 📊 Revised Effort Estimates

With suggested changes:

| Epic | Original Effort | Revised Effort | Change |
|------|----------------|----------------|---------|
| 1 | ~8 hrs | ~10 hrs | +2 (added Issue 1.5) |
| 2 | ~6 hrs | ~5 hrs | -1 (removed Issue 2.4) |
| 3 | ~7 hrs | ~9 hrs | +2 (added Issue 3.4, better scope) |
| 4 | ~9 hrs | ~10 hrs | +1 (added artifacts) |
| 5 | ~6 hrs | ~8 hrs | +2 (strategic review vs auto-triage) |
| **Total** | **36 hrs** | **42 hrs** | **+6 hrs** |

**Why +6 hours?**
- More thorough analysis (usage patterns, health reports)
- Strategic decision-making time
- Better artifacts (not just checklists)

**More accurate**: 42 hours accounts for actual work, not optimistic best-case

---

## 🎯 Critical Path Analysis

Your current sequencing shows everything in parallel, but there are **hard dependencies**:

```
Day 1-2: Issue 1.1 (Skills Catalog) ━━━━━┓
Day 1-2: Issue 1.2 (Commands Catalog) ━━━┫━━━> Issue 2.1 (Master Index)
Day 3:   Issue 1.3 (Symlinks) ━━━━━━━━━━━┛      ↓
                                               Day 4: Issue 2.2 (Maturity)
                                                     ↓
                                               Day 5: Issue 3.1 (Audit Workflows)
                                                     ↓
                                               Day 6: Issue 4.1 (Audit Skills)
                                                     ↓
                                               Day 7: Issue 5.1 (Strategic Review)
```

**True critical path**: ~7 days minimum (assuming 6 hrs/day focused work)

**Your Gantt shows**: 6 days (Feb 17-22)

**Recommendation**: Add 2 buffer days → Target completion Feb 24

---

## ✅ Recommendations Summary

### High Priority (Do Before Starting)
1. ✅ **Add Strategic Decision Framework** (use the one I created)
2. ✅ **Choose Path A/B/C** before starting Epic 1
3. ✅ **Merge Epics 3 & 4** into single "Resource Catalog" epic
4. ✅ **Replace Epic 5** with Strategic Review (not auto-implementation)
5. ✅ **Add Issue 1.5**: Documentation health validation
6. ✅ **Add Issue 3.4**: Workflow usage analysis

### Medium Priority (Improve Plan)
1. ⚠️ **Revise Issue 2.1**: Add implementation status column
2. ⚠️ **Revise Issue 3.1**: Use use-case based categories
3. ⚠️ **Revise Issue 4.3**: Add decision criteria (merge/deprecate/clarify)
4. ⚠️ **Add artifacts**: Skills Health Report, Workflow Usage Report
5. ⚠️ **Update effort**: 42 hours (not 36)
6. ⚠️ **Update timeline**: 9 days (not 6)

### Low Priority (Nice to Have)
1. 💡 Remove Issue 3.2 (project workflows) - premature
2. 💡 Add pre-commit hook for doc validation
3. 💡 Create dashboard view of skill/workflow health
4. 💡 Set up automated doc drift detection

---

## 🚀 Suggested Next Steps

1. **Read** the Strategic Decision Framework I created
2. **Discuss** with team (if applicable) which path makes sense
3. **Document decision** in framework doc
4. **Revise epic plan** based on chosen path and feedback above
5. **Start Epic 1** with confidence that you're on the right path

---

**Bottom Line**: Your plan is 85% excellent. The 15% gap is: (1) missing strategic decision, (2) premature Epic 5, (3) minor scope/sequencing improvements. Fix those three things and you have a bulletproof plan.
