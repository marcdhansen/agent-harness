---
title: "Enhance Core Tools for Coding Tasks"
labels: high-priority, tools, enhancement
priority: P1
---

## Problem Statement

Current 4 core tools (read, write, edit, bash) are basic and missing coding-specific capabilities:
- `edit` tool lacks validation and auto-formatting
- No way to search code structure (find functions/classes)
- No test execution tool
- No linting/code quality checks
- No git diff visualization
- No syntax validation before applying edits
- Missing rollback capability

## Proposed Solution

Enhance existing tools and add new coding-specific tools:

### Enhanced Edit Tool
```python
class EditTool:
    def execute(self, path: str, old_str: str, new_str: str):
        # Improvements:
        # 1. Syntax validation before applying
        # 2. Auto-formatting after edit (black, ruff)
        # 3. Show diff before applying (in debug mode)
        # 4. Automatic git commit with message
        # 5. Rollback capability
        
        # Validate syntax first
        if not self._is_valid_syntax(new_str, path):
            raise SyntaxError("New code has syntax errors")
        
        # Apply edit
        self._apply_edit(path, old_str, new_str)
        
        # Auto-format
        if self.auto_format:
            self._format_file(path)
        
        # Git commit (optional)
        if self.auto_commit:
            self._git_commit(path, f"Edit: {path}")
```

### New Coding-Specific Tools

1. **SearchCodeTool** - Find definitions
```python
class SearchCodeTool:
    """Find function/class definitions using AST"""
    def execute(self, query: str, file_pattern: str = "*.py"):
        # Use AST parsing, not just grep
        # Returns: file path, line number, definition
```

2. **RunTestsTool** - Execute tests
```python
class RunTestsTool:
    """Execute test suite and return results"""
    def execute(self, test_path: str = None):
        # Run pytest/unittest
        # Parse output
        # Return failures with context
        # Show coverage if available
```

3. **LintTool** - Check code quality
```python
class LintTool:
    """Run linters and return issues"""
    def execute(self, files: list[str], tools: list[str] = None):
        # Run: ruff, mypy, pylint
        # Aggregate results
        # Return actionable suggestions
```

4. **DiffTool** - Show changes
```python
class DiffTool:
    """Show git diff for current session"""
    def execute(self, files: list[str] = None, staged: bool = False):
        # Show what changed in session
        # Optionally filter by file
        # Syntax highlighted output
```

5. **SearchUsagesTool** - Find usages
```python
class SearchUsagesTool:
    """Find where a function/class is used"""
    def execute(self, symbol: str, scope: str = "project"):
        # Find all calls to function
        # Find all imports of module
        # Return with context (line before/after)
```

## Implementation Details

1. **Enhance EditTool**:
   - Add syntax validation using `ast` module
   - Integrate black/ruff for formatting
   - Add git integration (optional auto-commit)
   - Add preview mode (show diff, ask for confirmation)
   - Add rollback stack (undo last N edits)

2. **Implement SearchCodeTool**:
   - Use `ast` module to parse Python files
   - Support regex for function/class names
   - Return file paths with line numbers
   - Cache AST results for performance

3. **Implement RunTestsTool**:
   - Support pytest and unittest
   - Parse XML/JSON test output
   - Extract failure details
   - Support running specific tests
   - Show coverage percentage

4. **Implement LintTool**:
   - Integrate ruff (fast, modern)
   - Integrate mypy (type checking)
   - Optionally pylint
   - Parse output to structured format
   - Filter by severity

5. **Implement DiffTool**:
   - Use gitpython library
   - Show staged vs unstaged
   - Syntax highlight diffs
   - Support filtering by file

6. **Implement SearchUsagesTool**:
   - Use ripgrep for performance
   - Fallback to grep
   - Parse results with context
   - Group by file

## Tool Registration

```python
# In harness initialization
harness = InnerHarness(
    tools=[
        ReadTool(),
        WriteTool(),
        EditTool(auto_format=True, auto_commit=False),
        BashTool(),
        # New tools:
        SearchCodeTool(),
        RunTestsTool(),
        LintTool(),
        DiffTool(),
        SearchUsagesTool()
    ]
)
```

## Acceptance Criteria

### EditTool Enhancements
- [ ] Syntax validation before applying edits
- [ ] Auto-formatting works (black/ruff)
- [ ] Git auto-commit optional
- [ ] Preview mode shows diff
- [ ] Rollback capability (undo edits)

### New Tools
- [ ] SearchCodeTool finds function/class definitions
- [ ] RunTestsTool executes tests and parses output
- [ ] LintTool runs ruff/mypy and returns issues
- [ ] DiffTool shows git changes
- [ ] SearchUsagesTool finds symbol usages

### General
- [ ] All tools have comprehensive docstrings
- [ ] Error handling for edge cases
- [ ] Tests cover each tool
- [ ] Documentation includes examples
- [ ] Tools work in sandboxed environment

## Dependencies

- Issue #2 (Sandboxing) - tools must respect permissions
- Git skill (for auto-commit feature)

## Estimated Effort

Medium (1 week)

## Examples

```python
# Agent workflow with enhanced tools:

# 1. Search for function
search_code("parse_json")
# Returns: src/parser.py:45, src/utils.py:12

# 2. Find where it's used
search_usages("parse_json")
# Returns: 15 usages across 8 files

# 3. Edit with validation
edit_file(
    "src/parser.py",
    old_str="def parse_json(text):\n    return json.loads(text)",
    new_str="def parse_json(text):\n    try:\n        return json.loads(text)\n    except JSONDecodeError:\n        return None"
)
# Auto-validates syntax, formats, shows diff

# 4. Run tests
run_tests("tests/test_parser.py")
# Returns: 5 passed, 1 failed with traceback

# 5. Check lint
lint(["src/parser.py"])
# Returns: 2 warnings from ruff, 1 error from mypy

# 6. View changes
diff()
# Shows git diff with syntax highlighting
```

## Future Enhancements

- Refactoring tool (extract function, rename, etc.)
- Code metrics tool (complexity, coverage)
- Documentation generator
- Import optimizer
- Dead code detector
