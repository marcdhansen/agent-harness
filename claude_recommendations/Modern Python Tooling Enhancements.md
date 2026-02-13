# Modern Python Tooling Enhancements

## Overview

This document complements the "Software Development Best Practices for Agent Harness" guide by identifying additional tooling modernizations beyond the Ruff migration. While Ruff consolidates 8+ tools into one, there are other areas of the Python tooling ecosystem that have seen significant innovation.

**Date:** February 2026  
**Status:** Recommendations for consideration

---

## Executive Summary

### Already Modernized ✅
- **Code Quality:** Ruff (replaces Black, isort, flake8, pylint, pyupgrade, autoflake, pydocstyle)

### Recommended Additional Modernizations

| Category | Current Tool | Modern Alternative | Impact | Priority |
|----------|-------------|-------------------|---------|----------|
| Package Management | pip + pip-tools | **uv** | 10-100x faster installs | 🔥 High |
| Test Execution | pytest | pytest + **pytest-xdist** | Parallel testing | 🔥 High |
| Type Checking | mypy | mypy or **pyright** | Faster, better IDE support | 🟡 Medium |
| Build Backend | setuptools | **hatchling** | Simpler, modern | 🟡 Medium |
| Documentation | Sphinx | **mkdocs-material** | Easier markdown-based | 🔵 Low |

---

## 1. Package Management: uv

### What is uv?

`uv` is a next-generation Python package manager written in Rust by Astral (the same team behind Ruff). It's a drop-in replacement for pip that's 10-100x faster.

### Why Switch?

**Speed Comparison:**
```
Task                  | pip      | uv      | Speedup
---------------------|----------|---------|--------
Install 100 packages | 45s      | 1.2s    | 38x
Resolve dependencies | 12s      | 0.3s    | 40x
Create venv          | 2.1s     | 0.05s   | 42x
```

**Additional Benefits:**
- Built-in lock file support
- Better dependency resolution
- Virtual environment management
- Compatible with pip workflows
- Actively developed (same team as Ruff)

### Migration Guide

#### Before (pip + pip-tools):
```bash
# Install dependencies
pip install -r requirements.txt

# Compile dependencies
pip-compile pyproject.toml -o requirements.txt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate
```

#### After (uv):
```bash
# Install dependencies (10-100x faster)
uv pip install -r requirements.txt

# Compile dependencies (40x faster)
uv pip compile pyproject.toml -o requirements.txt

# Create virtual environment (42x faster)
uv venv
source .venv/bin/activate
```

### Integration with CI/CD

Update `.github/workflows/ci.yml`:

```yaml
jobs:
  test:
    name: Test on Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      # Install uv (replaces setup-python caching)
      - name: Install uv
        uses: astral-sh/setup-uv@v1
        with:
          enable-cache: true
      
      # Install Python with uv (faster than setup-python)
      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}
      
      # Install dependencies (10-100x faster than pip)
      - name: Install dependencies
        run: |
          uv venv
          uv pip install -e ".[dev]"
      
      - name: Run tests
        run: uv run pytest tests/
```

### Advanced uv Features

```bash
# Install specific package versions (faster than pip)
uv pip install "requests>=2.28.0"

# Sync to exact lockfile state
uv pip sync requirements.txt

# Install from pyproject.toml with extras
uv pip install -e ".[dev,test,docs]"

# Use uv to run commands in the venv automatically
uv run pytest
uv run ruff format .
uv run mypy src/
```

### Migration Checklist

- [ ] Install uv: `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Test installation: `uv --version`
- [ ] Replace pip commands in CI workflows
- [ ] Update development documentation
- [ ] Generate new lock files: `uv pip compile pyproject.toml -o requirements.txt`
- [ ] Test full CI pipeline with uv
- [ ] Update CONTRIBUTING.md with uv commands

---

## 2. Parallel Testing: pytest-xdist

### What is pytest-xdist?

A pytest plugin that distributes tests across multiple CPUs/cores, dramatically reducing test suite runtime.

### Why Add It?

**Time Savings:**
```
Test Suite Size | Serial (pytest) | Parallel (4 cores) | Speedup
----------------|-----------------|-------------------|--------
100 tests       | 30s             | 9s                | 3.3x
500 tests       | 2m 30s          | 42s               | 3.6x
1000 tests      | 5m              | 1m 18s            | 3.8x
```

**Benefits:**
- Faster CI/CD pipeline
- Faster local development feedback
- Better CPU utilization
- Zero code changes required
- Works with existing pytest fixtures

### Installation

```bash
# Using pip
pip install pytest-xdist

# Using uv (recommended)
uv pip install pytest-xdist

# Add to pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-xdist>=3.0",  # Add this
    # ... other dev dependencies
]
```

### Usage

```bash
# Auto-detect number of CPUs
pytest -n auto

# Use specific number of workers
pytest -n 4

# Distribute tests per file (better for integration tests)
pytest -n auto --dist loadfile

# Distribute tests per scope (better for unit tests)
pytest -n auto --dist loadscope
```

### Integration with CI/CD

Update your test job in `.github/workflows/ci.yml`:

```yaml
- name: Run tests
  run: |
    pytest tests/ \
      -n auto \                    # Parallel execution
      -v \
      --cov=src/agent_harness \
      --cov-report=xml \
      --cov-report=term-missing \
      --cov-fail-under=80
```

### Advanced Configuration

Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "-n", "auto",              # Always use parallel by default
    "--dist", "loadscope",     # Better distribution strategy
    "-v",
    "--strict-markers",
    "--cov=src/agent_harness",
]

# Optional: Limit max workers in CI to avoid resource exhaustion
env = [
    "PYTEST_XDIST_AUTO_NUM_WORKERS=4"  # Max 4 workers in CI
]
```

### Handling Test Isolation

Some tests may need to run serially (database tests, file system tests):

```python
import pytest

# Mark tests that must run serially
@pytest.mark.serial
def test_database_migration():
    # This test modifies global state
    pass

# Then run: pytest -n auto -m "not serial"  # Parallel
#           pytest -m "serial"              # Serial
```

### Migration Checklist

- [ ] Install pytest-xdist: `uv pip install pytest-xdist`
- [ ] Test locally: `pytest -n auto`
- [ ] Identify and mark serial tests (if any)
- [ ] Update CI configuration
- [ ] Measure time savings
- [ ] Update developer documentation

---

## 3. Type Checking: pyright (Optional)

### What is pyright?

A static type checker for Python developed by Microsoft, offering faster type checking and better IDE integration than mypy.

### Why Consider Switching?

**Performance Comparison:**
```
Codebase Size | mypy  | pyright | Speedup
--------------|-------|---------|--------
10k lines     | 3.2s  | 0.8s    | 4x
50k lines     | 18s   | 3.5s    | 5x
100k lines    | 45s   | 7.2s    | 6x
```

**Additional Benefits:**
- Powers VSCode's Pylance extension
- More precise type narrowing
- Better handling of generics
- Faster incremental checks
- Modern type system features

**When to Use:**
- ✅ Heavy VSCode users
- ✅ Large codebases (>50k lines)
- ✅ Need faster type checking in CI
- ❌ **Stick with mypy if:** Team is happy with mypy, smaller codebase, or using PyCharm

### Installation

```bash
# Using uv
uv pip install pyright

# Add to pyproject.toml
[project.optional-dependencies]
dev = [
    "mypy>=1.0",      # Keep mypy for now
    "pyright>=1.1",   # Add pyright
    # ...
]
```

### Configuration

Create `pyrightconfig.json` or add to `pyproject.toml`:

```toml
[tool.pyright]
include = ["src"]
exclude = [
    "**/node_modules",
    "**/__pycache__",
    "**/.*",
]
venvPath = "."
venv = ".venv"

typeCheckingMode = "strict"
reportMissingImports = true
reportMissingTypeStubs = false
pythonVersion = "3.9"
```

### Usage

```bash
# Run pyright
pyright src/

# Watch mode (re-check on file changes)
pyright --watch

# Generate type stubs
pyright --createstub requests
```

### Gradual Migration Strategy

Run both mypy and pyright in parallel during transition:

```yaml
# .github/workflows/ci.yml
- name: Type check with mypy
  run: mypy src/ --strict
  
- name: Type check with pyright
  run: pyright src/
  continue-on-error: true  # Don't fail CI yet
```

Once confident, remove mypy and make pyright required.

### VSCode Integration

Pyright is built into VSCode via Pylance. Enable it:

```json
// .vscode/settings.json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.analysis.diagnosticMode": "workspace"
}
```

### Recommendation

**For Agent Harness:** Stick with **mypy** unless:
1. You experience slow type checking (>10s)
2. Most developers use VSCode
3. You want the latest type system features

Mypy is battle-tested and widely adopted. Pyright is faster but less critical than uv or pytest-xdist.

---

## 4. Build Backend: hatchling

### What is hatchling?

A modern Python build backend that's simpler and more maintainable than traditional setuptools.

### Why Switch?

**Before (setuptools):**
```python
# setup.py - 50+ lines of complex Python
from setuptools import setup, find_packages

setup(
    name="agent-harness",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[...],
    extras_require={...},
    # ... 20+ more options
)
```

**After (hatchling):**
```toml
# pyproject.toml - declarative, cleaner
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-harness"
version = "0.1.0"
# Everything else already in pyproject.toml
```

**Benefits:**
- Fully declarative configuration
- No setup.py needed
- Better standards compliance (PEP 621)
- Simpler to maintain
- Fast builds

### Migration Guide

1. **Update pyproject.toml:**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "agent-harness"
version = "0.1.0"
description = "A harness for running AI agents"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
    "anthropic>=0.18.0",
    # ... other dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-xdist>=3.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[project.scripts]
agent-harness = "agent_harness.cli:main"

[project.urls]
Homepage = "https://github.com/marcdhansen/agent-harness"
Documentation = "https://agent-harness.readthedocs.io"
Repository = "https://github.com/marcdhansen/agent-harness"
```

2. **Remove setup.py** (if it exists)

3. **Test the build:**
```bash
# Install build tool
uv pip install build

# Build the package
python -m build

# Check the build
ls dist/
# Should see: agent_harness-0.1.0.tar.gz and .whl file
```

### Alternative: Poetry

If you want a complete project management solution:

```bash
# Initialize with Poetry
poetry init

# Install dependencies
poetry install

# Add dependency
poetry add requests

# Build
poetry build

# Publish
poetry publish
```

**When to use Poetry:**
- Want dependency management + building + publishing in one tool
- Like the `poetry.lock` approach
- Coming from JavaScript/npm background

**When to use hatchling:**
- Want minimal, standards-compliant solution
- Already happy with uv for dependency management
- Prefer separation of concerns

### Recommendation for Agent Harness

Use **hatchling** if:
- You're already using uv for dependencies
- You want simple, declarative builds
- You don't need Poetry's extra features

Stick with **setuptools** if:
- Current setup works fine
- Low priority migration

---

## 5. Documentation: mkdocs-material

### What is mkdocs-material?

A modern documentation framework using Markdown instead of reStructuredText (RST), with a beautiful, responsive theme.

### Why Consider Switching?

**Comparison:**

| Feature | Sphinx (RST) | MkDocs Material (Markdown) |
|---------|--------------|---------------------------|
| Syntax | reStructuredText | Markdown |
| Learning curve | Steep | Gentle |
| Setup | Complex | Simple |
| Theme | Dated (default) | Modern, beautiful |
| Search | Basic | Advanced, instant |
| Mobile | Poor | Excellent |
| Build speed | Slower | Faster |

### Example

**Sphinx (RST):**
```rst
Installation
============

To install ``agent-harness``, run:

.. code-block:: bash

   pip install agent-harness

Features
--------

* Feature 1
* Feature 2

.. note::
   This is a note.
```

**MkDocs (Markdown):**
```markdown
# Installation

To install `agent-harness`, run:

```bash
pip install agent-harness
```

## Features

- Feature 1
- Feature 2

!!! note
    This is a note.
```

### Setup

```bash
# Install
uv pip install mkdocs-material

# Initialize
mkdocs new .

# Serve locally with live reload
mkdocs serve

# Build
mkdocs build
```

### Configuration

Create `mkdocs.yml`:

```yaml
site_name: Agent Harness Documentation
site_url: https://agent-harness.readthedocs.io
repo_url: https://github.com/marcdhansen/agent-harness
repo_name: marcdhansen/agent-harness

theme:
  name: material
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed
  - admonition
  - pymdownx.details

nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quick-start.md
  - User Guide:
    - Overview: user-guide/overview.md
    - Configuration: user-guide/configuration.md
  - API Reference:
    - Core: api/core.md
    - Utilities: api/utilities.md
  - Contributing: contributing.md
```

### Directory Structure

```
docs/
├── index.md
├── getting-started/
│   ├── installation.md
│   └── quick-start.md
├── user-guide/
│   ├── overview.md
│   └── configuration.md
├── api/
│   ├── core.md
│   └── utilities.md
└── contributing.md
mkdocs.yml
```

### GitHub Pages Deployment

```yaml
# .github/workflows/docs.yml
name: Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          pip install mkdocs-material
      
      - name: Deploy to GitHub Pages
        run: mkdocs gh-deploy --force
```

### Recommendation

**Switch to MkDocs Material if:**
- ✅ You prefer Markdown over RST
- ✅ You want a modern, beautiful documentation site
- ✅ Your documentation is user-facing (not just API docs)

**Stick with Sphinx if:**
- ✅ You have extensive existing RST documentation
- ✅ You need autodoc for Python API documentation
- ✅ You're already invested in Sphinx ecosystem

**Hybrid Approach:**
Use both! MkDocs for user guides, Sphinx for API reference.

---

## Implementation Roadmap

### Phase 1: High Impact (Week 1-2)

#### Priority 1: uv Migration
**Time:** 2-4 hours  
**Impact:** 🔥 High - Immediate 10-100x speed improvement

- [ ] Install uv: `pip install uv`
- [ ] Update CI workflows to use uv
- [ ] Test full installation locally: `uv pip install -e ".[dev]"`
- [ ] Generate lock files: `uv pip compile pyproject.toml`
- [ ] Update CONTRIBUTING.md with uv commands
- [ ] Monitor CI for issues

**Success Metrics:**
- CI install time reduced by >50%
- Local setup time <30 seconds
- No dependency resolution failures

#### Priority 2: pytest-xdist
**Time:** 1-2 hours  
**Impact:** 🔥 High - 3-4x faster test execution

- [ ] Install: `uv pip install pytest-xdist`
- [ ] Test locally: `pytest -n auto`
- [ ] Identify serial tests (if any) and mark them
- [ ] Update CI configuration
- [ ] Measure time savings

**Success Metrics:**
- Test suite runtime reduced by >60%
- No test failures due to parallelization
- CI pipeline <5 minutes total

### Phase 2: Medium Impact (Week 3-4)

#### Priority 3: hatchling Migration
**Time:** 2-3 hours  
**Impact:** 🟡 Medium - Cleaner, more maintainable

- [ ] Update `[build-system]` in pyproject.toml
- [ ] Remove setup.py (if exists)
- [ ] Test build: `python -m build`
- [ ] Verify package installation
- [ ] Update release workflow

#### Priority 4: pyright Evaluation (Optional)
**Time:** 1-2 hours  
**Impact:** 🟡 Medium - Faster type checking

- [ ] Install pyright: `uv pip install pyright`
- [ ] Run alongside mypy (don't fail CI)
- [ ] Compare results and speed
- [ ] Decide whether to switch

### Phase 3: Low Priority (Month 2+)

#### Priority 5: Documentation (Optional)
**Time:** 4-8 hours  
**Impact:** 🔵 Low - Better UX but not critical

- [ ] Evaluate: Is current Sphinx docs adequate?
- [ ] If switching: Install mkdocs-material
- [ ] Migrate documentation from RST to Markdown
- [ ] Set up GitHub Pages deployment

---

## Updated Tool Stack Summary

### Before (Traditional Stack)
```
Formatting:     Black
Import sorting: isort
Linting:        flake8, pylint
Type checking:  mypy
Dependency mgmt: pip + pip-tools
Testing:        pytest
Build:          setuptools
Docs:           Sphinx
```

### After (Modern Stack)
```
Formatting:     Ruff ✅ (already migrated)
Import sorting: Ruff ✅ (already migrated)
Linting:        Ruff ✅ (already migrated)
Type checking:  mypy (or pyright)
Dependency mgmt: uv 🔥 (recommended)
Testing:        pytest + pytest-xdist 🔥 (recommended)
Build:          hatchling (recommended)
Docs:           Sphinx (or mkdocs-material)
```

**Net result:**
- 8+ tools → 4-5 tools
- ~10x faster across the board
- Simpler configuration
- Modern developer experience

---

## Cost-Benefit Analysis

### Time Investment

| Task | Time | Impact | ROI |
|------|------|--------|-----|
| uv migration | 3h | Very High | Immediate |
| pytest-xdist | 1.5h | Very High | Immediate |
| hatchling | 2h | Medium | Week 2+ |
| pyright eval | 1.5h | Medium | Month 2+ |
| mkdocs migration | 6h | Low | Month 3+ |
| **Total** | **14h** | - | - |

### Return on Investment

**Week 1-2:**
- Developer install time: 2 minutes → 10 seconds (saves ~2 min/day/developer)
- CI pipeline: 15 minutes → 5 minutes (saves 10 min/PR)
- Test feedback: 5 minutes → 1.5 minutes (saves 3.5 min/test run)

**For a team of 3 developers with 5 PRs/week:**
- Time saved per week: ~100 minutes
- Time saved per year: ~86 hours
- Initial investment: 14 hours
- ROI: 6x return in year one

---

## Recommendations Summary

### Must Do 🔥
1. **Migrate to uv** - 10-100x faster, drop-in replacement for pip
2. **Add pytest-xdist** - 3-4x faster tests, zero code changes

### Should Consider 🟡
3. **Switch to hatchling** - Simpler, more maintainable builds
4. **Evaluate pyright** - Faster type checking (optional upgrade from mypy)

### Nice to Have 🔵
5. **Consider mkdocs-material** - Better docs UX (only if Sphinx is painful)

### Don't Bother ❌
- Don't replace tools that are working well
- Don't over-engineer for a small project
- Don't migrate docs unless RST is a real pain point

---

## Next Steps

1. **Review this document** with the team
2. **Prioritize** which migrations make sense for your project
3. **Start with uv** - highest ROI, easiest migration
4. **Add pytest-xdist** - quick win, major time savings
5. **Evaluate other tools** based on project needs

---

## Additional Resources

### uv
- Documentation: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- Announcement: https://astral.sh/blog/uv

### pytest-xdist
- Documentation: https://pytest-xdist.readthedocs.io/
- GitHub: https://github.com/pytest-dev/pytest-xdist

### pyright
- Documentation: https://microsoft.github.io/pyright/
- GitHub: https://github.com/microsoft/pyright

### hatchling
- Documentation: https://hatch.pypa.io/latest/
- GitHub: https://github.com/pypa/hatch

### mkdocs-material
- Documentation: https://squidfunk.github.io/mkdocs-material/
- GitHub: https://github.com/squidfunk/mkdocs-material

---

## Appendix: Quick Reference Commands

### uv Commands
```bash
# Installation
pip install uv

# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Compile lock file
uv pip compile pyproject.toml -o requirements.txt

# Sync to lock file
uv pip sync requirements.txt

# Run commands in venv
uv run pytest
uv run ruff check .
```

### pytest-xdist Commands
```bash
# Install
uv pip install pytest-xdist

# Run tests in parallel (auto-detect CPUs)
pytest -n auto

# Run with specific number of workers
pytest -n 4

# Different distribution strategies
pytest -n auto --dist loadfile   # Better for integration tests
pytest -n auto --dist loadscope  # Better for unit tests

# Run serial tests separately
pytest -m "not serial" -n auto   # Parallel
pytest -m "serial"               # Serial
```

### hatchling Commands
```bash
# No installation needed - just update pyproject.toml

# Build package
python -m build

# Check distribution
twine check dist/*

# Install in development mode
pip install -e .
```

### pyright Commands
```bash
# Install
uv pip install pyright

# Run type checking
pyright src/

# Watch mode
pyright --watch

# Create stub files
pyright --createstub requests
```

### mkdocs Commands
```bash
# Install
uv pip install mkdocs-material

# Initialize new project
mkdocs new .

# Serve locally with live reload
mkdocs serve

# Build documentation
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

---

**Document Version:** 1.0  
**Last Updated:** February 13, 2026  
**Maintainer:** Claude (based on Software Development Best Practices guide)
