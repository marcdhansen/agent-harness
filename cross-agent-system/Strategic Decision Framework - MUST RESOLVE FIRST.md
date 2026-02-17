---
status: approved
implementation: complete
dependencies: []
---
# Strategic Decision Framework - MUST RESOLVE FIRST

**Date**: February 16, 2026  
**Context**: Cross-agent system has aspirational roadmap docs vs current working system  
**Decision Required**: Which path forward?

---

## 🔀 The Fork in the Road

You have two distinct paths. **Choose one before starting the epic plan:**

### Path A: Document Current State ("Accuracy-Only" Path)
**Goal**: Make docs 100% accurate to current working system, no major changes

**Scope**:
- Update SKILLS.md, COMMANDS.md to reflect all 24 skills and 12 workflows AS THEY ARE
- Fix SYMLINKS.md to match current architecture
- Add maturity/status markers to show what's stable vs experimental
- **Mark roadmap docs as "Future Vision - Not Implemented"**
- Focus: **Accuracy and discoverability of what exists today**

**Effort**: ~24 hours (Epics 1-4 only, simplified)

**Outcome**: Excellent documentation of working system, no transformation

**Choose this if**:
- Current system works well for your needs
- Not ready to invest in VFS/API/sandboxing changes
- Want clean docs before considering bigger changes
- Team needs to understand what exists first

---

### Path B: Implement Transformational Roadmap ("Build the Future" Path)
**Goal**: Evolve system toward VFS, API service, sandboxed support per roadmap

**Scope**:
- Do all of Epic 1-4 (document current state)
- **Actually implement** quick-wins (provider detection, structured logging, etc.)
- **Actually build** VFS to replace symlinks
- **Actually deploy** API service for sandboxed environments
- Integrate LangGraph, Temporal patterns, MCP
- **Use roadmap docs as implementation specs**

**Effort**: ~36 hours documentation + ~160 hours implementation = **~200 hours total**

**Outcome**: State-of-the-art universal agent system that works everywhere

**Choose this if**:
- Need to support sandboxed environments (Claude.ai web, GitHub Actions, etc.)
- Want to eliminate symlink fragility
- Ready to invest in significant architectural improvements
- Have resources for ~5 weeks of focused development

---

### Path C: Hybrid ("Staged Evolution" Path)
**Goal**: Document current state now, implement roadmap incrementally

**Scope**:
- Do all of Epic 1-4 first (get docs accurate)
- Mark roadmap docs as "Phase 2 - Future Implementation"
- Implement **only quick-wins** from roadmap (Week 7-8)
- Defer VFS/API/sandboxing to later decision
- Re-evaluate after quick-wins prove value

**Effort**: ~36 hours documentation + ~40 hours quick-wins = **~76 hours total**

**Outcome**: Excellent docs + immediate improvements + option to go bigger

**Choose this if**:
- Want to validate value before big investment
- Need improved docs urgently
- Can iterate toward transformation
- Prefer smaller, reversible steps

---

## 🎯 Recommended: Path C (Hybrid/Staged)

**Rationale**:
1. **Docs are foundation** - Can't plan transformation without understanding current state
2. **Quick-wins prove value** - Provider detection, logging, health checks are low-risk
3. **Preserves optionality** - Can decide on VFS/API after seeing quick-wins impact
4. **Reduces risk** - Avoids committing to 200-hour project before validating direction

**Modified Sequencing**:

```
Weeks 1-2: Epic 1 (Documentation Accuracy) ✅
  └─ Get complete, accurate picture of current system

Week 3: Epic 2 (Organization) + Epic 3-4 Merged ✅
  └─ Make everything navigable and categorized

Week 4: Strategic Review ⚡
  └─ Team reviews complete docs
  └─ Decides: stop here OR implement quick-wins OR full roadmap

IF implement quick-wins chosen:
  Weeks 5-6: Quick-wins Implementation
  └─ Provider detection, structured logging, health checks, state persistence
  
  Week 7: Measure Impact ⚡
  └─ Did quick-wins deliver value?
  └─ Decides: stop here OR continue to VFS/API

IF continue to VFS/API chosen:
  Weeks 8-10: VFS Implementation
  Weeks 11-13: API Service + Sandboxed Support
  Weeks 14-16: LangGraph/Temporal/MCP Integration
```

---

## 📋 Decision Documentation

**Record your decision here before proceeding:**

**Selected Path**: [ ] A - Accuracy Only  |  [ ] B - Full Transformation  |  [ ] C - Hybrid/Staged

**Decision Date**: _______________

**Decision Rationale**:
- 
- 
- 

**Success Criteria**:
- 
- 
- 

**Review Date**: _______________ (when to reassess)

---

## 🚨 Why This Decision Matters

**Without choosing a path**:
- Epic 5 (Roadmap-to-Implementation Pipeline) is **premature** - can't triage something you haven't committed to
- Epic 2.2 (Maturity Headers) needs different content for Path A vs Path B
- Epic 2.4 (Reconcile Quick-Wins) assumes you're implementing them
- Resource allocation is unclear (24 hrs vs 200 hrs)

**With a clear path**:
- Every epic has clear purpose
- Effort estimates are accurate
- Team knows what "done" looks like
- Can measure ROI properly

---

## 💡 Next Steps

1. **Read all 7 roadmap documents I created** (if not already done)
2. **Assess your constraints**:
   - Do you NEED sandboxed support? (Claude.ai web, GitHub Actions, etc.)
   - Are symlinks actually causing problems?
   - Do you have 5 weeks for transformation?
3. **Discuss with team** (if applicable)
4. **Make the decision** and document it above
5. **Adjust epic plan** based on chosen path
6. **Start Epic 1** (same regardless of path)

---

**Bottom Line**: Your epic plan is excellent for Path C (Hybrid). For Path A, simplify Epics 1-4 and skip Epic 5. For Path B, expand Epic 5 into actual implementation epics. **Choose first, then refine the plan accordingly.**
