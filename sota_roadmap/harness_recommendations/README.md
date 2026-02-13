# Agent Harness Improvement Issues

This directory contains detailed GitHub issue templates for improving the agent-harness system. These recommendations are based on a comprehensive analysis of the current system and comparison with state-of-the-art agent harness implementations.

## Quick Start

To create these issues in your GitHub repository:

### Option 1: Manual Creation
Copy the content of each `.md` file and create a new issue in your repository.

### Option 2: Using GitHub CLI
```bash
# Install gh if needed
brew install gh

# Authenticate
gh auth login

# Create all issues
for issue in issues/*.md; do
    gh issue create --repo marcdhansen/agent-harness \
        --title "$(head -2 $issue | tail -1 | sed 's/title: //' | tr -d '"')" \
        --body-file "$issue"
done
```

### Option 3: Using Python Script
```python
# See create_issues.py (included below)
```

---

## Issues by Priority

### 🔴 Critical Priority (P0) - Foundational

#### [#1: Multi-LLM Provider Abstraction Layer](01-multi-llm-provider-support.md)
**Effort:** Large (1-2 weeks)  
**Dependencies:** None  
**Status:** Not started

Create unified interface for multiple LLM providers (Anthropic, OpenAI, Google) with provider-specific optimizations.

**Why Critical:** You specified multi-provider support as "of critical importance"

---

#### [#2: Sandboxing and Permission System](02-sandboxing-permission-system.md)
**Effort:** Large (2 weeks)  
**Dependencies:** None  
**Status:** Not started

Implement multi-layer isolation using Colima/Lima containers and path-based permissions with human-in-loop approval.

**Why Critical:** Security is essential; currently unclear how dangerous operations are prevented

---

### 🟡 High Priority (P1) - Core Features

#### [#3: Debugging Capabilities](03-debugging-capabilities.md)
**Effort:** Medium (1 week)  
**Dependencies:** Issue #6 (Trajectory Logging)  
**Status:** Not started

Add interactive stepping, breakpoints, state inspection, time-travel debugging, and tool call tracing.

**Why High Priority:** You specifically requested this "as soon as possible"

---

#### [#4: Enhanced Coding Tools](04-enhanced-coding-tools.md)
**Effort:** Medium (1 week)  
**Dependencies:** Issue #2 (Sandboxing)  
**Status:** Not started

Enhance existing tools (edit, read, write, bash) and add coding-specific tools (search code, run tests, lint, diff).

**Why High Priority:** Core to coding-focused use case

---

#### [#5: Context Window Management](05-context-window-management.md)
**Effort:** Medium (1 week)  
**Dependencies:** Issue #1 (Multi-Provider)  
**Status:** Not started

Smart compression and eviction strategy for long coding sessions. Includes prompt caching support.

**Why High Priority:** Essential for long-running sessions without hitting context limits

---

#### [#6: Trajectory Logging](06-trajectory-logging.md)
**Effort:** Medium (1 week)  
**Dependencies:** None  
**Status:** Not started

Comprehensive JSONL logging of all agent actions with replay capability and analysis tools.

**Why High Priority:** Enables debugging, provides audit trail, supports Issue #3

---

#### [#7: Concurrent Agent Execution](07-concurrent-execution.md)
**Effort:** Medium (1 week)  
**Dependencies:** Issues #2, #8  
**Status:** Not started

Support running multiple agents concurrently without interference. Includes session isolation and resource limits.

**Why High Priority:** You specified concurrent execution as important requirement

---

#### [#8: Git Worktree Integration](08-git-worktree-integration.md)
**Effort:** Medium (5 days)  
**Dependencies:** None  
**Status:** Not started

Use git worktrees for agent workspace isolation with automatic version control and merge conflict detection.

**Why High Priority:** You specifically asked about this approach; provides elegant solution for concurrent agents

---

### 🟢 Medium Priority (P2) - Improvements

#### [#9: Simplify Architecture](09-simplify-architecture.md)
**Effort:** Medium (1 week)  
**Dependencies:** Should be done after Issues #1-8  
**Status:** Not started

Consolidate inner/outer harness into single unified architecture with execution modes.

**Why Medium Priority:** Improves developer experience but not blocking

---

#### [#10: Performance Metrics](10-performance-metrics.md)
**Effort:** Small (3-4 days)  
**Dependencies:** Issues #1, #6  
**Status:** Not started

Add comprehensive performance tracking including execution time, cost, token usage, and success rates.

**Why Medium Priority:** You said this would be "nice to have in the near future"

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
**Goal:** Critical security and flexibility features

1. **Week 1-2:** Issue #1 - Multi-LLM Provider Support
2. **Week 3-4:** Issue #2 - Sandboxing and Permission System

**Deliverables:**
- ✅ Works with Anthropic, OpenAI, Google
- ✅ Safe execution in Colima containers
- ✅ Permission system with HITL approval

---

### Phase 2: Developer Experience (Weeks 5-8)
**Goal:** Make development and debugging excellent

3. **Week 5:** Issue #3 - Debugging Capabilities
4. **Week 6:** Issue #4 - Enhanced Coding Tools
5. **Week 7:** Issue #6 - Trajectory Logging
6. **Week 8:** Issue #5 - Context Window Management

**Deliverables:**
- ✅ Interactive debugging with breakpoints
- ✅ Rich coding tools (search, test, lint)
- ✅ Full trajectory logging and replay
- ✅ Smart context management

---

### Phase 3: Scalability (Weeks 9-11)
**Goal:** Support concurrent execution

7. **Week 9:** Issue #8 - Git Worktree Integration
8. **Week 10:** Issue #7 - Concurrent Agent Execution
9. **Week 11:** Issue #10 - Performance Metrics

**Deliverables:**
- ✅ Git worktrees for isolation
- ✅ 3-5 concurrent agents supported
- ✅ Performance monitoring

---

### Phase 4: Polish (Week 12+)
**Goal:** Refinement and documentation

10. **Week 12:** Issue #9 - Simplify Architecture
11. **Ongoing:** Documentation, examples, testing

**Deliverables:**
- ✅ Unified, clean architecture
- ✅ Comprehensive docs
- ✅ Example projects

---

## Issue Dependencies Graph

```
#1: Multi-Provider (P0)
    ├─> #5: Context Management (P1)
    └─> #10: Performance Metrics (P2)

#2: Sandboxing (P0)
    ├─> #4: Enhanced Tools (P1)
    └─> #7: Concurrent Execution (P1)

#6: Trajectory Logging (P1)
    ├─> #3: Debugging (P1)
    └─> #10: Performance Metrics (P2)

#8: Git Worktrees (P1)
    └─> #7: Concurrent Execution (P1)

#1-#8: All Core Features
    └─> #9: Simplify Architecture (P2)
```

---

## Effort Estimation

| Priority | Total Effort | Issues |
|----------|--------------|--------|
| P0 (Critical) | 3-4 weeks | 2 issues |
| P1 (High) | 6-7 weeks | 6 issues |
| P2 (Medium) | 1.5-2 weeks | 2 issues |
| **Total** | **10-13 weeks** | **10 issues** |

*Note: Assumes single developer; can be parallelized for faster delivery*

---

## Quick Wins

If you want to see immediate impact, start with:

1. **Issue #3: Debugging Capabilities** (1 week) - Immediate developer productivity boost
2. **Issue #10: Performance Metrics** (3-4 days) - Quick visibility into what's happening
3. **Issue #4: Enhanced Coding Tools** (1 week) - Better tool support for coding tasks

These can be done in parallel with the foundational work on Issues #1 and #2.

---

## Next Steps

1. **Review issues** - Read through each `.md` file
2. **Prioritize** - Decide which to tackle first based on your needs
3. **Create in GitHub** - Use one of the methods above to create issues
4. **Assign labels** - Add priority, effort, and category labels
5. **Start development** - Pick the highest priority issue and begin!

---

## Contributing

When implementing these issues:

1. Create a feature branch: `feature/issue-N-short-description`
2. Reference the issue in commits: `git commit -m "feat: add debugging (#3)"`
3. Add tests for new features
4. Update documentation
5. Create PR linking to the issue

---

## Questions?

If you have questions about any issue:
- Comment on the GitHub issue
- Check the implementation details section
- Review the acceptance criteria
- Look at the examples in each issue

---

## License

These improvement proposals are provided as-is to help improve the agent-harness project.
