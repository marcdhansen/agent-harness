---
name: code-navigation
description: Techniques and tools for efficiently navigating codebases, finding functions/classes, understanding dependencies, and exploring project structure.
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

# 🧭 Code Navigation Skill

**Purpose**: Guide agents in efficiently exploring and understanding codebases to find relevant code quickly.

## 🎯 Mission

- Find functions, classes, and definitions quickly
- Understand code dependencies and imports
- Navigate project structure efficiently
- Identify usage patterns and call sites
- Map out codebase architecture

## 📋 When to Use This Skill

Use this skill when:
- Starting work in unfamiliar codebase
- Need to find where functionality is implemented
- Want to understand how components connect
- Looking for examples of specific patterns
- Refactoring code and need to find all usages
- Documenting system architecture

## 🔍 Finding Code

### Find Function/Class Definitions

```bash
# Using ripgrep (fast, recommended)
rg "def process_data" --type py

# Find class definitions
rg "class Parser" --type py

# Case-insensitive search
rg -i "userauth" --type py

# Using grep (fallback)
grep -r "def process_data" --include="*.py"
grep -r "class Parser" --include="*.py"

# Find with context (see lines before/after)
rg "def process_data" -A 5 -B 2  # 5 lines after, 2 before
```

### Find Function/Method Calls

```bash
# Find calls to function
rg "process_data\(" --type py

# Find method calls on objects
rg "\.transform\(" --type py

# Find constructor calls
rg "Parser\(" --type py

# Find with context to see how it's used
rg "\.save\(" -B 3 -A 1 --type py
```

### Find All Occurrences of Symbol

```bash
# Find all uses of variable/function/class
rg "\\buser_data\\b" --type py  # Word boundary for exact match

# Find in specific directory
rg "authenticate" src/auth/ --type py

# Find excluding test files
rg "process" --type py --glob '!test_*'
```

## 📦 Understanding Imports and Dependencies

### What Imports This Module?

```bash
# Find imports of specific module
rg "from auth import" --type py
rg "import auth" --type py

# Find all imports (any module)
rg "^import " --type py
rg "^from .* import" --type py

# Find relative imports
rg "from \\..*import" --type py
```

### What Does This Module Import?

```bash
# Show imports at top of file
head -30 src/parser.py | grep -E "^import |^from "

# Or with ripgrep
rg "^(import|from)" src/parser.py
```

### Visualize Dependencies

```bash
# Generate dependency graph (requires pydeps)
pip install pydeps
pydeps src/main.py --max-depth 2

# Or use grep to map imports
for file in src/**/*.py; do
    echo "=== $file ==="
    grep -E "^(import|from)" "$file"
done
```

## 🗂️ Project Structure Navigation

### Understand Directory Structure

```bash
# View directory tree
tree -L 3 -I '__pycache__|*.pyc|node_modules'

# Count files by type
find . -type f -name "*.py" | wc -l
find . -type f -name "*.js" | wc -l

# Find large files
find . -type f -name "*.py" -exec wc -l {} + | sort -rn | head -10

# Find recent changes
find . -name "*.py" -mtime -7  # Modified in last 7 days
```

### Project Organization Patterns

```bash
# Standard Python project
project/
├── src/              # Source code
│   ├── __init__.py
│   ├── main.py
│   └── module/
├── tests/            # Test files
│   └── test_*.py
├── docs/             # Documentation
├── setup.py          # Package config
└── requirements.txt  # Dependencies

# Find entry points
rg "if __name__ == '__main__':" --type py

# Find test files
find . -name "test_*.py"
find . -name "*_test.py"

# Find configuration files
find . -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.toml"
```

## 🔎 Searching Code Content

### Search for String Patterns

```bash
# Find TODO/FIXME comments
rg "TODO|FIXME|XXX|HACK" --type py

# Find SQL queries
rg "SELECT .* FROM" --type py

# Find API endpoints
rg "@app\.route" --type py
rg "def (get|post|put|delete)_" --type py

# Find error handling
rg "except.*:" --type py -A 2

# Find logging statements
rg "log\.(debug|info|warning|error|critical)" --type py
```

### Search for Code Patterns

```bash
# Find all class definitions with inheritance
rg "class \w+\(.+\):" --type py

# Find async functions
rg "async def" --type py

# Find decorators
rg "@\w+" --type py

# Find type hints
rg "def \w+\(.*\) -> " --type py

# Find comprehensions
rg "\[.+ for .+ in .+\]" --type py
```

## 🏗️ Understanding Code Architecture

### Identify Main Components

```bash
# Find major classes
rg "^class " --type py | cut -d: -f1 | sort -u

# Find modules with most definitions
for file in $(find src -name "*.py"); do
    count=$(rg "^(class|def) " "$file" | wc -l)
    echo "$count $file"
done | sort -rn | head -10

# Find external dependencies
grep -h "^import\|^from" src/**/*.py | sort -u
```

### Map Call Graphs

```bash
# Find what calls this function
function_name="process_data"
rg "$function_name\(" --type py

# Find what this function calls
rg "def $function_name" -A 20 --type py | rg "\w+\("

# Find inheritance hierarchy
rg "class.*\(BaseClass\)" --type py  # Find subclasses
```

### Identify Design Patterns

```bash
# Find singleton pattern
rg "class.*:.*_instance = None" --type py

# Find factory pattern
rg "def create_|factory" --type py -i

# Find observer pattern
rg "def notify|def subscribe|def register" --type py

# Find decorator pattern
rg "@\w+" -B 1 --type py | rg "^def"
```

## 🎯 IDE Navigation Features

### VS Code

```bash
# Quick file open
# Cmd/Ctrl + P → type filename

# Go to definition
# F12 or Cmd/Ctrl + Click on symbol

# Find all references
# Shift + F12 on symbol

# Go to symbol in file
# Cmd/Ctrl + Shift + O

# Go to symbol in workspace
# Cmd/Ctrl + T

# File structure/outline
# Cmd/Ctrl + Shift + O shows all symbols in file
```

### PyCharm

```bash
# Go to declaration
# Cmd + B or Cmd + Click

# Go to implementation
# Cmd + Alt + B

# Find usages
# Alt + F7

# File structure
# Cmd + F12

# Search everywhere
# Double Shift

# Navigate back/forward
# Cmd + Alt + Left/Right
```

### Command Line Navigation (Without IDE)

```bash
# Jump to function definition
function goto_definition() {
    local symbol=$1
    rg "def $symbol|class $symbol" --type py -n
}

goto_definition "process_data"
# Output: src/processor.py:45:def process_data(input):

# Find usage examples
function find_usage() {
    local symbol=$1
    rg "$symbol\(" --type py -B 2 -A 2
}

find_usage "Parser"
# Shows how Parser is instantiated with context
```

## 📊 Code Statistics

### Lines of Code

```bash
# Count lines by file type
find . -name "*.py" -exec wc -l {} + | sort -rn | head -20

# Total lines of Python code
find . -name "*.py" -exec wc -l {} + | tail -1

# Lines excluding comments and blank lines
find . -name "*.py" -exec grep -Ev "^\s*#|^\s*$" {} \; | wc -l
```

### Code Complexity

```bash
# Find long functions (potential complexity)
for file in $(find src -name "*.py"); do
    echo "=== $file ==="
    awk '/^def |^    def /{print NR,$0}' "$file"
done

# Count number of functions/classes per file
for file in $(find src -name "*.py"); do
    funcs=$(rg "^(def |class )" "$file" | wc -l)
    echo "$funcs $file"
done | sort -rn
```

### File Relationships

```bash
# Find most imported files
for file in $(find src -name "*.py"); do
    count=$(rg "from .* import |import " --count-matches "$file" 2>/dev/null | cut -d: -f2)
    echo "$count $file"
done | sort -rn | head -10

# Find files that import the most
for file in $(find src -name "*.py"); do
    imports=$(grep -E "^import |^from " "$file" | wc -l)
    echo "$imports $file"
done | sort -rn | head -10
```

## 🎓 Understanding Unfamiliar Code

### Entry Point Discovery

```bash
# Find main entry points
rg "if __name__ == '__main__':" --type py

# Find CLI entry points
rg "@click\.|@app\.|argparse\." --type py

# Find FastAPI/Flask routes
rg "@app\.(get|post|put|delete)" --type py

# Find pytest fixtures
rg "@pytest\.fixture" --type py
```

### Follow Code Flow

```bash
# Step 1: Find entry point
rg "if __name__ == '__main__':" src/main.py

# Step 2: See what main() does
rg "def main" src/main.py -A 20

# Step 3: For each function call, find definition
rg "def initialize" --type py

# Step 4: Repeat until you understand the flow
```

### Identify Core vs Utility Code

```bash
# Core business logic (usually in src/)
find src -name "*.py" -not -path "*/tests/*"

# Utility/helper code (look for "util", "helper", "common")
find . -name "*util*.py" -o -name "*helper*.py" -o -name "common.py"

# Configuration code
find . -name "config*.py" -o -name "settings.py"

# Test code
find . -name "test_*.py" -o -name "*_test.py"
```

## 🛠️ Advanced Navigation Techniques

### Technique 1: Grep with Context

```bash
# See function with its docstring and first few lines
rg "def process_data" -A 10 --type py

# See class with its methods
rg "class Parser" -A 50 --type py

# See import statements with what they're used for
rg "^from auth import" -A 5 --type py
```

### Technique 2: Find Dead Code

```bash
# Find functions that are never called
function find_unused() {
    for func in $(rg "^def (\w+)" --type py -r '$1' --no-filename | sort -u); do
        calls=$(rg "$func\(" --type py | wc -l)
        if [ $calls -eq 1 ]; then  # Only the definition
            echo "Possibly unused: $func"
        fi
    done
}
```

### Technique 3: Tag-Based Navigation

```bash
# Generate ctags (if available)
ctags -R src/

# Use ctags to jump to definitions
# In vim: Ctrl+] on symbol
# In emacs: M-. on symbol

# Or grep tags file
grep "process_data" tags
```

### Technique 4: Git History Navigation

```bash
# Find when function was added
git log -S "def process_data" --source --all

# See how function changed over time
git log -p -- src/processor.py | grep -A 20 "def process_data"

# Find who last modified function
git blame src/processor.py | grep -A 5 "def process_data"

# Find all files that changed with this file (related changes)
git log --format="" --name-only src/processor.py | sort -u
```

## 📝 Documentation for Navigation

### Generate Navigation Aids

```bash
# Create index of all functions
rg "^def (\w+)" --type py -r '$1' | sort > FUNCTIONS.txt

# Create index of all classes
rg "^class (\w+)" --type py -r '$1' | sort > CLASSES.txt

# Create module map
echo "# Module Map" > MODULE_MAP.md
for file in $(find src -name "*.py"); do
    echo "## $file" >> MODULE_MAP.md
    rg "^(def |class )" "$file" >> MODULE_MAP.md
    echo "" >> MODULE_MAP.md
done
```

### Document Navigation Patterns

```markdown
# Navigation Guide

## Entry Points
- `src/main.py`: Main application entry
- `src/cli.py`: Command-line interface
- `src/api.py`: REST API endpoints

## Core Modules
- `src/processor.py`: Data processing logic
- `src/database.py`: Database access layer
- `src/auth.py`: Authentication/authorization

## Finding Things
- Authentication code: `rg "auth" src/`
- Database queries: `rg "SELECT" src/`
- API endpoints: `rg "@app.route" src/`
```

## ✅ Navigation Checklist

When starting in new codebase:
- [ ] Find and read README
- [ ] Identify entry points (main, CLI, API)
- [ ] Understand project structure (src, tests, docs)
- [ ] Locate configuration files
- [ ] Find core business logic
- [ ] Identify external dependencies
- [ ] Check for documentation (docs/, README)

When looking for specific functionality:
- [ ] Search for related terms (rg/grep)
- [ ] Check obvious locations first (e.g., auth code in src/auth/)
- [ ] Look for tests (often show usage examples)
- [ ] Check imports (what does this module depend on?)
- [ ] Follow call chain (who calls this? what does this call?)

## 🚫 Navigation Anti-Patterns

### ❌ Reading Files Top-to-Bottom

```bash
# Bad: Open random file and read sequentially
cat src/huge_file.py | less  # Overwhelming

# Good: Search for what you need
rg "def specific_function" src/huge_file.py -A 10
```

### ❌ Guessing File Locations

```bash
# Bad: Guess where code might be
cat src/auth.py  # Might not exist

# Good: Search for it
rg "def authenticate" --type py
# Shows exact file and line number
```

### ❌ Not Using Search Tools

```bash
# Bad: Manual grep every time
grep -r "some_function" . --include="*.py" | grep -v test | grep -v __pycache__

# Good: Use ripgrep with built-in filters
rg "some_function" --type py
# Automatically excludes common ignore patterns
```

## 🔗 Integration with Other Skills

- **Debugging Skill**: Navigate to bug location quickly
- **Refactoring**: Find all usages before refactoring
- **Testing**: Locate relevant test files
- **Git Skill**: Use git blame/log for navigation

## 🛠️ Recommended Tools

### Essential

- **ripgrep (rg)**: Fast code search - `brew install ripgrep`
- **fd**: Fast file find - `brew install fd`
- **tree**: Directory visualization - `brew install tree`

### Optional

- **fzf**: Fuzzy finder - `brew install fzf`
- **ag (silver searcher)**: Alternative to ripgrep
- **ctags**: Tag-based navigation
- **pydeps**: Python dependency visualization

### IDE Extensions

- **VS Code**: Python, Pylance (type checking)
- **PyCharm**: Built-in navigation features
- **Vim**: ctags, fzf.vim, coc.nvim

---

**Remember**: The goal is not to read every line of code, but to quickly find the relevant parts you need to understand or modify.
