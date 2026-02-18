# Coding Principles

These principles guide all code development in the agent harness system.

## 1. Prevent, Detect, Correct

A three-layered approach to managing code quality and bugs.

### Prevent

- Write clean, readable code from the start
- Use type hints to catch type-related bugs early
- Add assertions to validate assumptions
- Use pre-commit hooks to block bad code before it enters the codebase

### Detect

- Write comprehensive tests (unit, integration, e2e)
- Run linters and formatters automatically
- Enable type checking (mypy/pyright)
- Use code coverage tools to identify untested code

### Correct

- Fix bugs promptly when discovered
- Don't defer bug fixes unless absolutely necessary
- Add regression tests to prevent reoccurrence
- Document the fix and its rationale

## 2. Fail Loudly

Errors must be visible and actionable. Silent failures hide problems that need to be fixed.

### Principles

- **Never silently fall back**: When something fails, report the failure clearly
- **Use explicit error messages**: Say what went wrong, not just that it went wrong
- **Fail fast**: Detect errors early, at the point of failure
- **Return error codes**: Scripts and functions should signal success/failure clearly

### Examples

```python
# BAD: Silent fallback
def get_config():
    if not os.path.exists("config.json"):
        return {}  # Silent failure - caller doesn't know config is missing

# GOOD: Fail loudly
def get_config():
    if not os.path.exists("config.json"):
        raise FileNotFoundError("config.json not found. Please create it from config.example.json")
```

```bash
# BAD: Script succeeds even on error
./some-script.sh 2>/dev/null

# GOOD: Script fails with clear error
./some-script.sh || { echo "Script failed with code $?"; exit 1; }
```

### When to Catch Exceptions

- At the boundary of your system (API handlers, CLI entry points)
- When you can actually recover from the error
- Never catch exceptions just to log and re-raise

## 3. Treat the Cause, Not the Symptom

Fix root causes, not just the visible problem. This prevents recurrence and often reveals larger issues.

### The Pattern

When you encounter a bug:

1. **Don't just fix the symptom**: Fixing what's broken is never enough
2. **Find the root cause**: Ask "why did this happen?" multiple times
3. **Fix the root cause**: Update the code that allowed the bug to occur
4. **Add preventive measures**: Pre-commit hooks, assertions, validation, tests

### Example

**Symptom**: CI fails because `changelog.json` has corrupted data

**Wrong approach**: Just fix the corrupted data in changelog.json

**Right approach**:
1. What wrote the corrupted data? Find the script
2. Why did it write invalid data? Missing validation?
3. Fix the script to validate before writing
4. Add a pre-commit hook to validate JSON files before commit
5. Add a test to verify the script produces valid output

### Early Detection in Development Cycle

Catch problems as early as possible:

| Stage | Detection Method |
|-------|-----------------|
| Editor | LSP, inline errors |
| Pre-commit | Hooks, linting |
| Commit | CI checks |
| PR | Code review |
| Merge | Post-merge CI |
| Deploy | Staging environment |

The earlier you catch problems, the cheaper they are to fix.

## 4. SOP Documents: Agent-Optimized but Human-Usable

Scripts, AGENTS.md, and SOP documentation should be:

- **Machine-readable**: Structured for agent parsing and execution
- **Human-readable**: Clear enough for humans to understand and follow
- **Optimized for agents**: Use consistent patterns, clear commands, parseable formats
- **Human-friendly**: Include context, explanations, and rationale

### Examples

- Use clear command structures
- Include usage examples
- Add comments explaining why

## 5. Scripts Optimized for Agents, Not Humans

Agents cannot wait for human input. Scripts must be autonomous.

### Requirements

- [ ] No blocking for user input (use flags with defaults)
- [ ] Support `--help` for documentation
- [ ] Use exit codes for success/failure
- [ ] Accept configuration via flags or config files
- [ ] Be idempotent (safe to run multiple times)
- [ ] Log clearly for debugging
- [ ] Include `--dry-run` option for dangerous operations
