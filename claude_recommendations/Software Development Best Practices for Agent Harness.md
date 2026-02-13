# Software Development Best Practices for Agent Harness

## Current State Assessment

Based on the repository structure:
- ✅ Has: Python package structure (src/agent_harness)
- ✅ Has: Tests directory
- ✅ Has: pyproject.toml
- ✅ Has: Examples
- ❌ Missing: CI/CD pipeline
- ❌ Missing: Automated testing
- ❌ Missing: Code quality enforcement (Ruff)
- ❌ Missing: Release automation
- ❌ Missing: Documentation infrastructure

**Tooling Philosophy:** This guide uses **Ruff** as the modern, all-in-one solution for formatting and linting, replacing Black, isort, flake8, pylint, pyupgrade, and autoflake. Ruff is 10-100x faster and has become the industry standard.

---

## I. CI/CD Pipeline (Priority 1)

### A. GitHub Actions Workflows

Create `.github/workflows/` directory with these workflows:

#### 1. Main CI Pipeline

**`.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    name: Test on Python ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run tests
        run: |
          pytest tests/ \
            -v \
            --cov=src/agent_harness \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=80
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-${{ matrix.python-version }}
  
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run Ruff linter
        run: ruff check src/ tests/
      
      - name: Run Ruff formatter check
        run: ruff format --check src/ tests/
      
      - name: Run mypy
        run: mypy src/ --strict
  
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run bandit
        run: bandit -r src/ -ll
      
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit
  
  docs:
    name: Documentation
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
          pip install sphinx sphinx-rtd-theme
      
      - name: Build documentation
        run: |
          cd docs
          make html
      
      - name: Check for broken links
        run: |
          cd docs
          make linkcheck
```

#### 2. Release Workflow

**`.github/workflows/release.yml`**

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    name: Build Distribution
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Check distribution
        run: twine check dist/*
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
  
  publish-pypi:
    name: Publish to PyPI
    needs: build
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write
    
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
  
  create-release:
    name: Create GitHub Release
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Download artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      
      - name: Extract changelog
        id: changelog
        run: |
          # Extract version from tag
          VERSION=${GITHUB_REF#refs/tags/v}
          
          # Extract changelog section for this version
          sed -n "/## \[$VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1 > release-notes.md
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          body_path: release-notes.md
          draft: false
          prerelease: false
```

#### 3. Dependency Update

**`.github/workflows/dependency-update.yml`**

```yaml
name: Dependency Update

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  update-dependencies:
    name: Update Dependencies
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      
      - name: Install pip-tools
        run: pip install pip-tools
      
      - name: Compile dependencies
        run: |
          pip-compile pyproject.toml --upgrade -o requirements.txt
          pip-compile pyproject.toml --extra dev --upgrade -o requirements-dev.txt
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: 'chore: update dependencies'
          title: 'chore: weekly dependency update'
          body: |
            Automated dependency update
            
            - Updated all dependencies to latest compatible versions
            - Review changes before merging
          branch: dependency-updates
          labels: dependencies
```

#### 4. PR Validation

**`.github/workflows/pr-validation.yml`**

```yaml
name: PR Validation

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  validate-pr:
    name: Validate PR
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Check PR title
        uses: amannn/action-semantic-pull-request@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          types: |
            feat
            fix
            docs
            style
            refactor
            perf
            test
            build
            ci
            chore
      
      - name: Check for changelog entry
        run: |
          if ! git diff origin/main...HEAD -- CHANGELOG.md | grep -q "^+"; then
            echo "❌ No changelog entry found"
            echo "Please add an entry to CHANGELOG.md"
            exit 1
          fi
      
      - name: Validate commits
        run: |
          # Check commits follow conventional commits
          for commit in $(git rev-list origin/main..HEAD); do
            message=$(git log --format=%B -n 1 $commit | head -n 1)
            if ! echo "$message" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|build|ci|chore)(\(.+\))?!?: .+'; then
              echo "❌ Invalid commit message: $message"
              echo "Use conventional commits format"
              exit 1
            fi
          done
      
      - name: Check for breaking changes
        run: |
          if git diff origin/main...HEAD | grep -q "BREAKING CHANGE"; then
            echo "⚠️ Breaking change detected - ensure version bump is major"
          fi
```

---

## II. Code Quality Configuration

### A. pyproject.toml Updates

Add these sections to your existing `pyproject.toml`:

```toml
[project]
name = "agent-harness"
version = "0.1.0"
description = "Standard Agentic Protocol (SAP) Harness for AI Agent Orchestration"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Marc D Hansen", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "pydantic>=2.0.0",
    "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "hypothesis>=6.98.0",
    
    # Code quality (Ruff replaces: black, isort, flake8, pylint, pyupgrade, autoflake)
    "ruff>=0.8.0",
    "mypy>=1.8.0",
    
    # Security
    "bandit>=1.7.0",
    
    # Documentation
    "sphinx>=7.2.0",
    "sphinx-rtd-theme>=2.0.0",
    "sphinx-autodoc-typehints>=2.0.0",
    
    # Pre-commit
    "pre-commit>=3.6.0",
]

[project.urls]
Homepage = "https://github.com/marcdhansen/agent-harness"
Documentation = "https://agent-harness.readthedocs.io"
Repository = "https://github.com/marcdhansen/agent-harness"
Issues = "https://github.com/marcdhansen/agent-harness/issues"

[build-system]
requires = ["setuptools>=68.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.ruff]
line-length = 100
target-version = "py39"

# Exclude directories
extend-exclude = [
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".tox",
    ".venv",
    "build",
    "dist",
]

[tool.ruff.lint]
# Enable these rule sets
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
    "TCH",   # flake8-type-checking
    "PTH",   # flake8-use-pathlib
    "RUF",   # Ruff-specific rules
    "PL",    # pylint
]

# Ignore specific rules
ignore = [
    "E501",    # Line too long (handled by formatter)
    "PLR0913", # Too many arguments to function call
    "PLR2004", # Magic value used in comparison
]

# Allow fix for all enabled rules (when `--fix` is provided)
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401"]  # Unused imports in __init__.py
"tests/*" = ["S101", "PLR2004"]  # Use of assert and magic values in tests

[tool.ruff.lint.isort]
known-first-party = ["agent_harness"]
force-single-line = false
lines-after-imports = 2

[tool.ruff.format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces, not tabs
indent-style = "space"

# Respect magic trailing commas
skip-magic-trailing-comma = false

# Automatically detect the appropriate line ending
line-ending = "auto"

# Enable auto-formatting of code examples in docstrings
docstring-code-format = true

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true
strict_concatenate = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
pythonpath = ["src"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/examples/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
precision = 2
show_missing = true

[tool.bandit]
exclude_dirs = ["/tests"]
skips = ["B101"]  # assert_used (common in tests)
```

### B. Pre-commit Configuration

**`.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: detect-private-key
      - id: mixed-line-ending
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      # Run the linter
      - id: ruff
        args: [--fix]
      # Run the formatter
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-ll', '-r', 'src/']
  
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

---

## III. Testing Infrastructure

### A. Pytest Configuration

Create `tests/conftest.py`:

```python
"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path
from typing import Generator

@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Generator[Path, None, None]:
    """Create temporary workspace for tests."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    yield workspace


@pytest.fixture
def mock_llm():
    """Mock LLM for testing without API calls."""
    from unittest.mock import Mock
    
    llm = Mock()
    llm.invoke.return_value = "Mock response"
    return llm


@pytest.fixture
def sample_harness_config():
    """Sample configuration for testing."""
    return {
        "process_id": "TEST-001",
        "description": "Test process",
        "llm_client": None,
    }
```

### B. Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests
│   ├── test_inner_harness.py
│   ├── test_outer_harness.py
│   ├── test_tools.py
│   └── test_state.py
├── integration/                # Integration tests
│   ├── test_full_workflow.py
│   └── test_persistence.py
├── fixtures/                   # Test data
│   ├── sample_graphs.py
│   └── sample_tasks.py
└── performance/                # Performance tests
    └── test_benchmarks.py
```

### C. Example Test

**`tests/unit/test_inner_harness.py`**

```python
"""Tests for InnerHarness."""
import pytest
from agent_harness import InnerHarness


class TestInnerHarness:
    """Test suite for InnerHarness."""
    
    def test_initialization(self, mock_llm):
        """Test harness initializes correctly."""
        harness = InnerHarness(llm_client=mock_llm)
        assert harness.llm_client is not None
    
    def test_run_simple_task(self, mock_llm):
        """Test running a simple task."""
        harness = InnerHarness(llm_client=mock_llm)
        result = harness.run("Print hello world")
        assert result is not None
    
    @pytest.mark.slow
    def test_complex_workflow(self, mock_llm):
        """Test complex multi-step workflow."""
        harness = InnerHarness(llm_client=mock_llm)
        # ... complex test ...
```

---

## IV. Documentation Infrastructure

### A. Sphinx Documentation

Create `docs/` directory:

```
docs/
├── conf.py              # Sphinx configuration
├── index.rst            # Documentation homepage
├── api/                 # API reference
│   ├── index.rst
│   └── modules.rst
├── guides/              # User guides
│   ├── quickstart.rst
│   ├── installation.rst
│   └── configuration.rst
└── examples/            # Example usage
    └── basic_usage.rst
```

**`docs/conf.py`**

```python
"""Sphinx configuration."""
import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'Agent Harness'
copyright = '2025, Marc D Hansen'
author = 'Marc D Hansen'
version = '0.1.0'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'langgraph': ('https://langchain-ai.github.io/langgraph/', None),
}

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}
```

### B. README Improvements

Update `README.md` with:

```markdown
# Agent Harness

[![CI](https://github.com/marcdhansen/agent-harness/workflows/CI/badge.svg)](https://github.com/marcdhansen/agent-harness/actions)
[![codecov](https://codecov.io/gh/marcdhansen/agent-harness/branch/main/graph/badge.svg)](https://codecov.io/gh/marcdhansen/agent-harness)
[![PyPI version](https://badge.fury.io/py/agent-harness.svg)](https://badge.fury.io/py/agent-harness)
[![Python versions](https://img.shields.io/pypi/pyversions/agent-harness.svg)](https://pypi.org/project/agent-harness/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Standard Agentic Protocol (SAP) Harness for AI Agent Orchestration.

[Installation](#installation) | [Documentation](https://agent-harness.readthedocs.io) | [Examples](examples/) | [Contributing](CONTRIBUTING.md)

## Features

- ✅ Two-tier architecture (Inner & Outer harness)
- ✅ LangGraph-powered orchestration
- ✅ Human-in-the-loop workflows
- ✅ SQLite-backed persistence
- ✅ Extensible tool system

## Quick Start

\```python
pip install agent-harness
\```

\```python
from agent_harness import InnerHarness

harness = InnerHarness(llm_client=my_llm)
result = harness.run("Your task here")
\```

See [documentation](https://agent-harness.readthedocs.io) for details.

## Development

\```bash
# Clone repository
git clone https://github.com/marcdhansen/agent-harness.git
cd agent-harness

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/agent_harness

# Format and lint code
ruff format src/ tests/
ruff check --fix src/ tests/

# Type check
mypy src/
\```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
```

---

## V. Release Management

### A. Semantic Versioning

Follow [SemVer](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### B. CHANGELOG.md

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial CI/CD pipeline setup
- Code quality tooling (black, isort, mypy, flake8)
- Comprehensive test suite
- Sphinx documentation

### Changed
- Updated README with badges and better structure

### Fixed
- None

## [0.1.0] - 2025-02-13

### Added
- Initial release
- Inner Harness implementation
- Outer Harness with LangGraph
- Basic tool system
- SQLite persistence
```

### C. Version Bumping Script

**`scripts/bump_version.sh`**

```bash
#!/bin/bash
# Bump version across project files

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/bump_version.sh <version>"
    echo "Example: ./scripts/bump_version.sh 0.2.0"
    exit 1
fi

NEW_VERSION=$1

# Update pyproject.toml
sed -i.bak "s/version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Update __init__.py
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$NEW_VERSION\"/" src/agent_harness/__init__.py

# Update docs/conf.py
sed -i.bak "s/version = '.*'/version = '$NEW_VERSION'/" docs/conf.py
sed -i.bak "s/release = '.*'/release = '$NEW_VERSION'/" docs/conf.py

# Cleanup backup files
rm -f pyproject.toml.bak src/agent_harness/__init__.py.bak docs/conf.py.bak

echo "✅ Version bumped to $NEW_VERSION"
echo "Next steps:"
echo "1. Update CHANGELOG.md"
echo "2. git add ."
echo "3. git commit -m 'chore: bump version to $NEW_VERSION'"
echo "4. git tag v$NEW_VERSION"
echo "5. git push && git push --tags"
```

---

## VI. Additional Best Practices

### A. Issue Templates

**`.github/ISSUE_TEMPLATE/bug_report.md`**

```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. 
2. 
3. 

**Expected behavior**
What you expected to happen.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python version: [e.g. 3.11]
 - Agent Harness version: [e.g. 0.1.0]

**Additional context**
Add any other context about the problem here.
```

### B. Pull Request Template

**`.github/pull_request_template.md`**

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Checklist

- [ ] My code follows the style guidelines (black, isort, mypy)
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have updated the CHANGELOG.md

## Related Issues

Closes #(issue number)
```

### C. Contributing Guidelines

**`CONTRIBUTING.md`**

```markdown
# Contributing to Agent Harness

Thank you for your interest in contributing!

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/agent-harness.git`
3. Create a virtual environment: `python -m venv venv`
4. Activate: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
5. Install dev dependencies: `pip install -e ".[dev]"`
6. Install pre-commit hooks: `pre-commit install`

## Development Workflow

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Make your changes
3. Run tests: `pytest`
4. Format and lint: `ruff format . && ruff check --fix .`
5. Type check: `mypy src/`
6. Commit changes (use conventional commits)
7. Push to your fork
8. Open a pull request

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`

## Code Style

- Use Ruff for formatting and linting (replaces Black, isort, flake8, pylint)
- Line length: 100 characters
- Type hints required (enforced by mypy --strict)
- Docstrings required (Google style)

```bash
# Format code
ruff format .

# Lint and auto-fix
ruff check --fix .

# Type check
mypy src/
```

## Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest fixtures for common setup
- Mock external dependencies

## Pull Request Process

1. Update CHANGELOG.md
2. Ensure CI passes
3. Request review from maintainers
4. Address review comments
5. Squash commits before merge (if requested)
```

---

## VII. Implementation Checklist

### Week 1: Foundation
- [ ] Create `.github/workflows/ci.yml`
- [ ] Update `pyproject.toml` with dev dependencies (including Ruff)
- [ ] Create `.pre-commit-config.yaml` (with Ruff)
- [ ] Install pre-commit hooks: `pre-commit install`
- [ ] Format code: `ruff format .`
- [ ] Lint and fix: `ruff check --fix .`
- [ ] Verify CI passes

### Week 2: Testing
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Organize tests into unit/integration folders
- [ ] Write tests for core functionality (aim for 80% coverage)
- [ ] Add pytest configuration to `pyproject.toml`
- [ ] Verify CI runs tests successfully

### Week 3: Documentation
- [ ] Create `docs/` directory with Sphinx setup
- [ ] Write API documentation
- [ ] Create user guides
- [ ] Add examples
- [ ] Set up ReadTheDocs integration

### Week 4: Release Process
- [ ] Create CHANGELOG.md
- [ ] Create version bumping script
- [ ] Set up PyPI publishing in GitHub Actions
- [ ] Create first tagged release
- [ ] Publish to PyPI

### Ongoing
- [ ] Review and merge dependency updates
- [ ] Monitor CI failures
- [ ] Update documentation as features change
- [ ] Respond to issues and PRs

---

## VIII. Metrics & Monitoring

### A. GitHub Repository Badges

Add to README.md:

```markdown
[![CI](https://github.com/marcdhansen/agent-harness/workflows/CI/badge.svg)](https://github.com/marcdhansen/agent-harness/actions)
[![codecov](https://codecov.io/gh/marcdhansen/agent-harness/branch/main/graph/badge.svg)](https://codecov.io/gh/marcdhansen/agent-harness)
[![Code Quality](https://api.codacy.com/project/badge/Grade/YOUR_PROJECT_ID)](https://www.codacy.com/gh/marcdhansen/agent-harness)
[![PyPI version](https://badge.fury.io/py/agent-harness.svg)](https://badge.fury.io/py/agent-harness)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

### B. Code Coverage

Set up Codecov:

1. Sign up at https://codecov.io
2. Add repository
3. Add `CODECOV_TOKEN` to GitHub secrets
4. Coverage automatically uploaded by CI

### C. Code Quality

Set up Codacy:

1. Sign up at https://www.codacy.com
2. Connect GitHub repository
3. Automatic code quality analysis

---

## IX. Cost-Benefit Analysis

**Time Investment:**
- Initial setup: ~20 hours
- Ongoing maintenance: ~2 hours/week

**Benefits:**
- 🚀 **Faster development**: Catch bugs before merge
- 📈 **Code quality**: Consistent style, fewer bugs
- 🔒 **Security**: Automated vulnerability scanning
- 📚 **Documentation**: Always up-to-date docs
- 🎯 **Reliability**: Automated testing prevents regressions
- 👥 **Collaboration**: Clear contribution guidelines
- 🏷️ **Releases**: Automated, repeatable release process

**ROI Timeline:**
- Month 1: Setup costs > benefits
- Month 2-3: Breaking even
- Month 4+: Significant time savings from automation

---

## X. Why Ruff?

This guide uses **Ruff** as the all-in-one linting and formatting solution. Here's why:

### Consolidation

**Ruff replaces 8+ tools:**
- Black (formatting)
- isort (import sorting)
- flake8 (linting)
- pylint (linting)
- pyupgrade (Python syntax modernization)
- autoflake (unused import removal)
- pydocstyle (docstring linting)
- flake8-bugbear, flake8-comprehensions, etc. (additional checks)

**Before (multiple tools):**
```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
pylint src/ tests/
pyupgrade --py39-plus $(find src -name "*.py")
```

**After (one tool):**
```bash
ruff format .           # Formatting
ruff check --fix .      # Linting with auto-fix
```

### Performance

Ruff is written in Rust and is **10-100x faster** than Python-based tools:

| Task | Traditional Tools | Ruff | Speedup |
|------|------------------|------|---------|
| Format 10k lines | 2.3s (Black) | 0.08s | 29x |
| Sort imports | 1.1s (isort) | 0.08s | 14x |
| Lint | 3.5s (flake8) | 0.12s | 29x |
| **Total** | **6.9s** | **0.2s** | **35x** |

### Configuration Simplicity

**Before:** Multiple config sections across multiple files
```toml
[tool.black]
line-length = 100

[tool.isort]
profile = "black"
line_length = 100

[tool.flake8]  # Actually in setup.cfg
max-line-length = 100

[tool.pylint]
max-line-length = 100
```

**After:** Single unified config
```toml
[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM", "RUF", "PL"]
```

### Industry Adoption

Major projects using Ruff (as of 2025):
- FastAPI
- Pydantic  
- Pandas
- Apache Airflow
- Bokeh
- Transformers (Hugging Face)

### Black Compatibility

Ruff's formatter is **Black-compatible by default**. You can switch from Black to Ruff with zero code changes.

### Auto-fix Capabilities

Ruff can automatically fix hundreds of issues:
- Import sorting
- Unused imports removal
- Unnecessary list comprehensions
- f-string conversions
- Type annotation improvements
- And much more...

```bash
# Fix all auto-fixable issues
ruff check --fix .
```

### Developer Experience

**Better error messages:**
```
Black: "cannot format file.py: Cannot parse: 1:0"

Ruff: "file.py:1:1: SyntaxError: Expected an expression
    │
  1 │ def foo(
    │         ^ Unexpected end of file"
```

**Integrated tooling:**
- One pre-commit hook instead of 3-4
- One CI step instead of 5-6
- One command to run locally

### Migration Path

Extremely easy to migrate from Black + isort + flake8:

```bash
# 1. Install
pip install ruff

# 2. Uninstall old tools
pip uninstall black isort flake8 pylint

# 3. Format (identical to Black)
ruff format .

# 4. Lint with auto-fix
ruff check --fix .

# 5. Update configs (see examples above)
```

**Expected code changes:** Minimal to none if using standard Black config.

---

## XI. Summary

## XI. Summary

**Critical Path (Do First):**

1. **CI Pipeline** (2 hours)
   - Create `.github/workflows/ci.yml`
   - Test, lint (Ruff), security jobs

2. **Ruff Setup** (1 hour)
   - Install Ruff: `pip install ruff`
   - Configure in `pyproject.toml`
   - Format existing code: `ruff format .`
   - Fix issues: `ruff check --fix .`

3. **Pre-commit Hooks** (30 min)
   - Install pre-commit
   - Configure Ruff hooks
   - Test on sample commit

4. **Test Infrastructure** (4 hours)
   - Organize test structure
   - Write basic tests
   - Get coverage >80%

5. **Documentation** (4 hours)
   - Set up Sphinx
   - Write basic API docs
   - Improve README

6. **Release Process** (2 hours)
   - Create CHANGELOG
   - Set up release workflow
   - Document versioning

**Total initial investment: ~13.5 hours for critical path.**

After this, you'll have:
- ✅ Automated testing on every PR
- ✅ Modern code quality enforcement (Ruff - 35x faster than old tools)
- ✅ Security vulnerability scanning
- ✅ Documentation site
- ✅ Automated releases
- ✅ Simpler tooling (1 tool instead of 8)

This transforms the repository from "personal project" to "professional open-source software."
