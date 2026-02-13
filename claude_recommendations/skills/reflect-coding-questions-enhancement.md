# Reflect Skill - Coding-Specific Strategic Questions Enhancement

## Purpose

Add technical and coding-focused strategic questions to complement the existing excellent process-focused questions.

## Integration

Add this section to reflect/SKILL.md after the existing "Strategic Analysis Questions" section:

---

## 🖥️ Technical & Coding-Specific Strategic Questions

These questions complement the existing strategic questions with technical depth. During reflection, agents should explicitly address both process AND technical dimensions.

### Code Quality & Technical Debt

>**QUESTION**: What code smells or anti-patterns did you encounter during this session?

Consider:
- Duplicated code that could be DRY'd up
- Long functions (>50 lines) that should be split
- Deep nesting (>3 levels) that hurts readability
- Magic numbers/strings that should be constants
- Poor variable/function naming
- Missing error handling

**Example Reflection**:
```markdown
Code Smells Identified:
- `process_data()` function is 120 lines (should be <50)
- Password validation duplicated in 3 places
- Database connection logic repeated in every module
- Magic number "86400" used instead of constant SECONDS_PER_DAY
```

>**QUESTION**: Which functions or modules exceeded acceptable complexity? (Cyclomatic complexity >10, cognitive complexity >15)

Consider:
- Functions with many conditional branches
- Deep nesting structures
- Long parameter lists (>5 parameters)
- Classes with too many responsibilities (>10 methods)

**Example Reflection**:
```markdown
High Complexity Functions:
- `authenticate_user()`: CC=15 (too many auth methods checked)
  → Recommendation: Use strategy pattern for auth methods
- `parse_request()`: CC=12 (handles too many formats)
  → Recommendation: Split into format-specific parsers
```

>**QUESTION**: What technical debt did this session introduce or address?

Consider:
- Quick hacks or workarounds added
- TODOs/FIXMEs introduced
- Deprecated API usage
- Missing tests (test debt)
- Incomplete refactoring
- Documentation gaps

**Example Reflection**:
```markdown
Technical Debt Added:
- Added TODO in auth.py line 45: "Refactor to use async"
- Temporary workaround for cache invalidation (needs proper solution)

Technical Debt Paid Down:
- Removed 3 deprecated API calls
- Added missing tests for edge cases
- Documented complex algorithm in parser.py
```

### Testing Strategy

>**QUESTION**: What test coverage gaps were revealed during this session?

Consider:
- Edge cases not covered
- Integration test gaps
- Missing negative test cases
- Flaky or intermittent test failures
- Performance test coverage

**Example Reflection**:
```markdown
Test Coverage Gaps:
- No tests for empty input handling
- Missing integration test for auth + database
- Performance tests needed for large dataset scenarios
- No tests for concurrent access patterns
```

>**QUESTION**: Did any tests fail spuriously? Why?

Consider:
- Race conditions in tests
- Hard-coded timing assumptions
- Order dependencies between tests
- External service dependencies
- Database state not properly reset

**Example Reflection**:
```markdown
Flaky Tests Identified:
- `test_async_notification()` fails 10% of time
  → Cause: Race condition with message queue
  → Fix: Add proper sync primitives
- `test_api_response_time()` fails in CI
  → Cause: CI server slower than dev machine
  → Fix: Increase timeout threshold
```

>**QUESTION**: What testing patterns worked well? What didn't?

Consider:
- Test fixtures that were helpful
- Mocking strategies that simplified tests
- Test utilities that increased productivity
- Test organization that improved clarity

**Example Reflection**:
```markdown
Testing Patterns That Worked:
- Factory pattern for test data simplified setup
- Parameterized tests caught more edge cases efficiently
- Context managers for database cleanup worked well

Testing Patterns That Didn't Work:
- Mocking entire database was brittle
  → Better: Use test database with known state
- Trying to test UI and logic together
  → Better: Separate UI tests from business logic tests
```

### Performance & Optimization

>**QUESTION**: Were there performance bottlenecks identified during this session?

Consider:
- Slow database queries (>100ms)
- N+1 query problems
- Inefficient algorithms (wrong time complexity)
- Unnecessary API calls
- Memory leaks or high memory usage
- CPU-intensive operations blocking I/O

**Example Reflection**:
```markdown
Performance Issues Found:
- User profile page making 50+ queries (N+1 problem)
  → Fix: Use eager loading / join
- JSON parsing taking 2s for 10MB file
  → Fix: Use streaming parser
- Search query taking 5s on 1M records
  → Fix: Add database index on search columns
```

>**QUESTION**: What optimization opportunities exist but weren't pursued?

Consider:
- Caching opportunities (query results, computed values)
- Lazy loading possibilities
- Batch processing opportunities
- Parallel processing possibilities
- Database query optimization
- Algorithm improvements (better data structures)

**Example Reflection**:
```markdown
Optimization Opportunities (Future Work):
- User permissions could be cached (currently queried every request)
- Image thumbnails could be pre-generated instead of on-demand
- Report generation could be background job instead of synchronous
- API responses could use compression (20% size reduction)
```

### Architecture & Design

>**QUESTION**: Did this work reveal coupling between modules that should be separated?

Consider:
- Modules that know too much about each other's internals
- Changes that required touching many files
- Circular dependencies
- Modules that can't be tested independently
- Shared mutable state

**Example Reflection**:
```markdown
Coupling Issues Identified:
- Auth module directly imports database models
  → Creates circular dependency
  → Recommendation: Use repository pattern
- Notification service tightly coupled to email implementation
  → Can't add SMS without changing notification code
  → Recommendation: Use strategy pattern for notification channels
```

>**QUESTION**: What abstractions could reduce duplication or improve clarity?

Consider:
- Common patterns that could be extracted
- Base classes or interfaces that could unify approaches
- Utility functions that could be shared
- Design patterns that could simplify code

**Example Reflection**:
```markdown
Abstraction Opportunities:
- All API clients have similar retry logic
  → Create RetryableClient base class
- Validation logic duplicated across forms
  → Create Validator abstraction
- Database migrations have common patterns
  → Create migration helper utilities
```

>**QUESTION**: Are there opportunities for dependency injection to improve testability?

Consider:
- Hard-coded dependencies (database, external services)
- Global state that makes testing difficult
- Constructor parameters that could enable easier mocking
- Service locator vs dependency injection

**Example Reflection**:
```markdown
Dependency Injection Opportunities:
- Parser class creates database connection internally
  → Pass database connection in constructor
  → Enables testing with mock database
- Email service uses global SMTP configuration
  → Inject configuration object
  → Enables testing with mock email sender
```

### Git & Version Control

>**QUESTION**: Were commits atomic and well-described?

Consider:
- One logical change per commit
- Clear commit messages following conventions
- Commits that mix unrelated changes
- Work-in-progress commits that should be squashed

**Example Reflection**:
```markdown
Git Quality Assessment:
✅ Good:
- All commits follow conventional commit format
- Each commit compiles and tests pass

❌ Issues:
- One commit mixed refactoring + bug fix
  → Should have been 2 commits
- Several "WIP" commits need squashing before merge
```

>**QUESTION**: Were there merge conflicts? Could they have been avoided?

Consider:
- Conflicts due to working on same files
- Conflicts due to not rebasing often enough
- Conflicts due to formatting differences
- Patterns to avoid conflicts in future

**Example Reflection**:
```markdown
Merge Conflict Analysis:
- Conflict in models.py due to two features adding fields
  → Could avoid: Better communication about current work
- Conflict in imports due to auto-formatter differences
  → Could avoid: Team should use same formatter config
- No conflicts in modular code (good separation)
```

>**QUESTION**: What branching strategy issues arose?

Consider:
- Branch naming clarity
- Branch lifetime (stale branches)
- Feature branch size (too large?)
- Integration timing (waiting too long?)

**Example Reflection**:
```markdown
Branching Issues:
- Feature branch lived for 3 weeks
  → Too long, harder to merge
  → Better: Break into smaller incremental features
- Branch name "fix-stuff" not descriptive
  → Better: "bugfix/fix-memory-leak-in-parser"
```

### Tool & Environment

>**QUESTION**: What development tools would have helped during this session?

Consider:
- Missing IDE features or extensions
- Debugging tools needed
- Testing tools lacking
- Build or deployment tools missing
- Documentation tools inadequate

**Example Reflection**:
```markdown
Tool Gaps:
- Need better profiler for finding performance bottlenecks
  → Recommendation: Install py-spy
- Missing type checker integration in IDE
  → Recommendation: Configure mypy in VS Code
- No database query analyzer
  → Recommendation: Enable Django Debug Toolbar
```

>**QUESTION**: Were there environment setup or configuration issues?

Consider:
- Dependency conflicts
- Version mismatches
- Missing environment variables
- Database setup problems
- Service configuration issues

**Example Reflection**:
```markdown
Environment Issues:
- Python 3.9 on CI but 3.11 locally
  → Caused syntax compatibility issues
  → Fix: Standardize on 3.11
- Redis connection failing in tests
  → Was configured for production host
  → Fix: Add test-specific Redis config
```

## 🎯 Enhanced Reflection Template

Use this comprehensive template during reflection:

```markdown
# Session Reflection: [ISSUE-ID]

## Session Summary
- **Duration**: X hours
- **Outcome**: [Success/Partial/Blocked]
- **Files Modified**: N files (+X/-Y lines)

## Process Learnings (Existing)
[Use existing strategic questions about SOP, cognitive load, etc.]

## Technical Learnings (New)

### Code Quality
- Code smells: [List]
- High complexity: [Functions with CC>10]
- Technical debt: [Added/Paid down]

### Testing
- Coverage gaps: [List]
- Flaky tests: [Issues found]
- Testing patterns: [What worked/didn't]

### Performance
- Bottlenecks: [Found issues]
- Optimization opportunities: [Future work]

### Architecture
- Coupling issues: [Problems found]
- Abstraction opportunities: [Improvements identified]
- Design patterns: [Applications]

### Git & Version Control
- Commit quality: [Assessment]
- Merge conflicts: [Analysis]
- Branching: [Issues]

### Tools & Environment
- Tool gaps: [Missing tools]
- Environment issues: [Problems encountered]

## Quantitative Results
- Lines of code: +X/-Y
- Test coverage: Z% (ΔW%)
- Complexity: N functions >10 CC
- Performance: Query time X→Y ms

## Action Items
- [ ] [Refactoring task]
- [ ] [Tool to install]
- [ ] [Technical debt to address]
- [ ] [Test to add]
```

## Benefits of Technical Questions

1. **Deeper Learning**: Capture technical insights, not just process
2. **Quality Improvement**: Systematically identify code quality issues
3. **Knowledge Transfer**: Technical patterns documented for reuse
4. **Proactive Improvement**: Find issues before they become problems
5. **Skill Development**: Agents learn what good code looks like

## Integration with Existing Questions

These technical questions **complement** (not replace) existing strategic questions about:
- SOP simplification effectiveness
- Cognitive load reduction
- Multi-agent collaboration
- Process improvements

Use BOTH sets of questions for comprehensive reflection.
