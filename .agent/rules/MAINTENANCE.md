# Maintenance Plan

This document defines the systematic maintenance practices for the agent-harness project, covering test coverage, code quality, refactoring, architecture reviews, and performance profiling.

For coding standards and principles, see [coding-principles.md](./coding-principles.md).

---

## 1. Test Coverage

### Target
- **Initial Target**: 60% code coverage
- **Growth Strategy**: Increase by 5% quarterly until reaching 80%

### Enforcement
- All PRs must maintain or increase coverage
- Coverage is reported in CI via `pytest-cov`
- Coverage below threshold blocks PR merge

### Measurement
```bash
# Run with coverage
pytest --cov=src/agent_harness --cov-report=term-missing

# Check coverage percentage
pytest --cov=src/agent_harness --cov-report=term --cov-fail-under=60
```

### What to Test
- All new code requires unit tests
- Bug fixes must include regression tests
- Critical paths (initialization, finalization, state management) require 80%+ coverage

---

## 2. Code Review

### Cadence
- **On-PR**: All changes require review before merge
- **Weekly Review Session**: Dedicated time for reviewing outstanding PRs

### Checklist
Every code review must evaluate:

- [ ] **Functionality**: Does the code work as intended?
- [ ] **Test Coverage**: Are there adequate tests?
- [ ] **Refactoring Target**: Does any touched code need refactoring? (See Section 3)
- [ ] **Type Safety**: Are type hints correct and complete?
- [ ] **Security**: Any security concerns?
- [ ] **Performance**: Any obvious performance issues?
- [ ] **Documentation**: Are docs updated if needed?

### Review Assignment
- Primary: Author of PR requests review
- Fallback: Team rotation or random assignment
- P0 issues: Require immediate review assignment

---

## 3. Refactoring

### Cadence
- **Weekly**: Part of every code review
- **On-Touch**: Any code an agent touches must be evaluated for refactoring

### Evaluation Criteria
Every piece of code touched during a session should be evaluated for:

| Criterion | Questions |
|-----------|-----------|
| **Readability** | Is the code easy to understand? Are names clear? |
| **Duplication** | Is there repeated logic that could be extracted? |
| **Complexity** | Are functions/modules too large? Can they be split? |
| **Coupling** | Is there unnecessary coupling between modules? |
| **Technical Debt** | Any obvious debt that was introduced? |

### Refactoring Priorities
1. **High Priority**: Code that blocks feature development
2. **Medium Priority**: Repeated patterns across codebase
3. **Low Priority**: Naming improvements, minor cleanup

### Tracking
- Refactoring tasks should be captured as beads issues
- Large refactoring should be tracked in ROADMAP.md

---

## 4. Architecture Review

### Cadence
- **Monthly**: Dedicated architecture review session

### Focus Areas
- Module boundaries and separation of concerns
- Dependency direction (should point inward, not outward)
- API design consistency
- State management patterns
- Error handling approaches

### Review Checklist
- [ ] Are module boundaries clear?
- [ ] Is dependency injection used appropriately?
- [ ] Are there circular dependencies?
- [ ] Is there appropriate abstraction?
- [ ] Do new features fit the existing architecture?

### Output
- Document findings in `.agent/docs/architecture-review-{date}.md`
- Create beads issues for significant findings
- Update architecture decisions in README.md or ADRs

---

## 5. Type Checking

### Tool
- **mypy**: Static type checker for Python

### Configuration
```toml
[tool.mypy]
python_version = "3.11"
strict = false
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

### CI Integration
- Run mypy in CI pipeline
- Type errors block PR merge
- New code should include type hints

### Best Practices
- Use `Any` sparingly
- Prefer explicit types over inference for public APIs
- Run mypy locally before pushing: `mypy src/agent_harness/`

---

## 6. Profiling

### Cadence
- **Weekly**: Performance check during development
- **On-Change**: After significant code changes

### What to Profile
- Execution time of critical paths
- Memory usage patterns
- Database/query performance
- API response times

### Tools
- Python's `cProfile` for CPU profiling
- `memory_profiler` for memory usage
- LangGraph built-in profiling for agent execution

### Tracking
- Log performance baselines in `.agent/docs/performance/`
- Create beads issues for performance regressions
- Include profiling results in retrospective

---

## 7. Security Scanning

### Current Setup
- **Bandit**: Security linter in CI pipeline
- Runs on every PR
- Medium/High severity issues block merge

### Best Practices
- Never introduce known vulnerable dependencies
- Review Bandit output on every PR
- Address high-severity findings immediately

---

## 8. Maintenance Schedule Summary

| Activity | Frequency | Trigger |
|----------|-----------|---------|
| Test coverage check | On-PR + CI | Every PR |
| Refactoring evaluation | Weekly + On-touch | Every code review |
| Profiling | Weekly | Development cycle |
| Architecture review | Monthly | Scheduled session |
| Type checking | On-PR + CI | Every PR |
| Security scanning | On-PR + CI | Every PR |
| Dependency audit | Quarterly | Scheduled |

---

## 9. TDD Enforcement

Test-Driven Development is mandatory for all feature implementation:

### Requirements
- Write failing test first (Red phase)
- Write minimum code to pass (Green phase)
- Refactor while keeping tests passing (Refactor phase)

### In Code Review
- Verify tests exist for new code
- Verify tests were written before implementation
- Verify tests cover edge cases

### Coverage Expansion
When implementing a feature:
- Write tests for the new functionality
- Add tests for related existing code (expand coverage)
- Add regression tests for any bugs fixed

---

## 10. Quality Gates

All PRs must pass these gates before merge:

1. ✅ All tests pass (`pytest`)
2. ✅ Coverage at or above threshold (`pytest-cov`)
3. ✅ No linting errors (`ruff`)
4. ✅ No type errors (`mypy`)
5. ✅ No security issues (`bandit`)
6. ✅ Code review approved
7. ✅ Refactoring evaluation completed

---

## References

- [coding-principles.md](./coding-principles.md) - Coding standards
- [ROADMAP.md](./ROADMAP.md) - Project roadmap
- [SOP_COMPLIANCE_CHECKLIST.md](./docs/SOP_COMPLIANCE_CHECKLIST.md) - SOP compliance
- [pyproject.toml](../../pyproject.toml) - Test and coverage configuration
