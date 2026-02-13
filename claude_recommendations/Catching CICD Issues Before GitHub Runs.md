# Catching CI/CD Issues Before GitHub Runs

## The Problem

CI/CD failures on GitHub Actions waste time and resources:
- **Feedback delay**: 2-10 minutes per failed run
- **Context switching**: Breaking flow to fix issues
- **Resource waste**: GitHub Actions minutes consumed
- **Embarrassment**: Broken builds visible to team
- **Iteration cost**: Multiple push-wait-fix cycles

**Solution:** Catch issues locally before pushing.

---

## I. Quick Wins (Implement These First)

### A. Pre-Commit Hooks

**Problem:** Committing code that will obviously fail CI/CD.

**Solution:** Run checks before commits are created.

#### 1. Install pre-commit Framework

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << 'EOF'
repos:
  # Code formatting
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  # Linting
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100']

  # YAML validation
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict

  # Security scanning
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
EOF

# Install hooks
pre-commit install
```

**Now every `git commit` automatically runs these checks.**

#### 2. Custom Pre-Commit Hook (Shell Script)

For projects without pre-commit framework:

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash

echo "Running pre-commit checks..."

# Run tests
echo "→ Running tests..."
if ! pytest tests/ -q; then
    echo "❌ Tests failed. Commit aborted."
    exit 1
fi

# Check code formatting
echo "→ Checking formatting..."
if ! black --check .; then
    echo "❌ Code formatting issues found. Run: black ."
    exit 1
fi

# Lint code
echo "→ Linting..."
if ! flake8 .; then
    echo "❌ Linting failed."
    exit 1
fi

# Check for debugging artifacts
echo "→ Checking for debugging artifacts..."
if git diff --cached | grep -E "(debugger|pdb.set_trace|console.log|FIXME|TODO)"; then
    echo "⚠️  Warning: Found debugging artifacts in staged files"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ All pre-commit checks passed!"
EOF

chmod +x .git/hooks/pre-commit
```

### B. Pre-Push Hooks

**Problem:** Passing local tests doesn't guarantee CI will pass.

**Solution:** Run CI-equivalent checks before pushing.

```bash
# Create .git/hooks/pre-push
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash

echo "Running pre-push checks (simulating CI)..."

# Full test suite (not just quick tests)
echo "→ Running full test suite..."
if ! pytest tests/ --cov=src --cov-report=term-missing; then
    echo "❌ Full test suite failed. Push aborted."
    exit 1
fi

# Build check (catches missing dependencies, import errors)
echo "→ Checking build..."
if [ -f "setup.py" ]; then
    if ! python setup.py build; then
        echo "❌ Build failed. Push aborted."
        exit 1
    fi
elif [ -f "pyproject.toml" ]; then
    if ! pip install -e .[dev] --dry-run; then
        echo "❌ Dependency resolution failed. Push aborted."
        exit 1
    fi
fi

# Type checking
echo "→ Running type checks..."
if ! mypy src/; then
    echo "❌ Type checking failed. Push aborted."
    exit 1
fi

# Security audit
echo "→ Running security audit..."
if [ -f "requirements.txt" ]; then
    if ! pip-audit; then
        echo "⚠️  Security vulnerabilities found. Review before pushing."
        read -p "Push anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

echo "✅ All pre-push checks passed!"
EOF

chmod +x .git/hooks/pre-push
```

---

## II. Local CI/CD Simulation

### A. Act - Run GitHub Actions Locally

**Problem:** GitHub Actions have specific environments that differ from local.

**Solution:** Use `act` to run GitHub Actions workflows locally.

#### Installation

```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (with Chocolatey)
choco install act-cli
```

#### Usage

```bash
# List all workflows and jobs
act -l

# Run default workflow (usually 'push')
act

# Run specific workflow
act -j test

# Run with specific event
act pull_request

# Use specific platform (matches GitHub runners)
act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest

# Dry run (see what would run)
act -n

# Run with secrets (create .secrets file)
cat > .secrets << EOF
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://localhost/test
EOF

act --secret-file .secrets

# Debug mode (verbose output)
act -v
```

#### Common Issues with Act

```bash
# Issue: Docker not running
# Fix: Start Docker Desktop

# Issue: "unable to find image"
# Fix: Pull the image first
docker pull ghcr.io/catthehacker/ubuntu:act-latest

# Issue: Act uses different default shell
# Fix: Specify shell in workflow
# jobs:
#   test:
#     steps:
#       - run: |
#           #!/bin/bash
#           set -e
#           pytest tests/

# Issue: Missing environment variables
# Fix: Create .env file and load in act
act --env-file .env
```

### B. GitLab CI - gitlab-runner exec

For GitLab CI pipelines:

```bash
# Install gitlab-runner
# macOS
brew install gitlab-runner

# Linux
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
sudo apt-get install gitlab-runner

# Run job locally
gitlab-runner exec docker test

# Run with custom Docker image
gitlab-runner exec docker --docker-image python:3.11 test
```

### C. Jenkins - Jenkins CLI

For Jenkins pipelines:

```bash
# Download Jenkins CLI
wget http://jenkins-server/jnlpJars/jenkins-cli.jar

# Validate Jenkinsfile syntax
java -jar jenkins-cli.jar -s http://jenkins-server declarative-linter < Jenkinsfile

# Use Jenkins Docker for local testing
docker run -p 8080:8080 jenkins/jenkins:lts
# Then test pipeline through web UI
```

---

## III. CI/CD Configuration Validation

### A. YAML Linting

**Problem:** Syntax errors in CI configuration files.

**Solution:** Validate YAML before pushing.

```bash
# Install yamllint
pip install yamllint

# Create .yamllint config
cat > .yamllint << EOF
extends: default

rules:
  line-length:
    max: 120
  indentation:
    spaces: 2
  comments:
    min-spaces-from-content: 1
EOF

# Validate GitHub Actions workflows
yamllint .github/workflows/*.yml

# Validate GitLab CI
yamllint .gitlab-ci.yml

# Add to pre-commit
cat >> .pre-commit-config.yaml << EOF
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
        args: ['-d', '{extends: default, rules: {line-length: {max: 120}}}']
EOF
```

### B. GitHub Actions Validation

```bash
# Install actionlint
# macOS
brew install actionlint

# Linux
bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)

# Validate workflows
actionlint .github/workflows/*.yml

# Check for specific issues
actionlint -shellcheck= .github/workflows/ci.yml  # Skip shellcheck
actionlint -pyflakes= .github/workflows/ci.yml    # Skip pyflakes

# Add to pre-commit
cat >> .pre-commit-config.yaml << EOF
  - repo: https://github.com/rhysd/actionlint
    rev: v1.6.26
    hooks:
      - id: actionlint
EOF
```

### C. Docker Configuration Validation

**Problem:** Dockerfile errors only caught during CI build.

**Solution:** Lint and test Docker builds locally.

```bash
# Install hadolint
# macOS
brew install hadolint

# Linux
wget -O /usr/local/bin/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
chmod +x /usr/local/bin/hadolint

# Validate Dockerfile
hadolint Dockerfile

# Test build locally
docker build -t myapp:test .

# Test with BuildKit (faster, catches more issues)
DOCKER_BUILDKIT=1 docker build -t myapp:test .

# Test multi-stage builds
docker build --target production -t myapp:prod .

# Check image size
docker images myapp:test --format "{{.Size}}"

# Scan for vulnerabilities
docker scan myapp:test

# Add to pre-commit
cat >> .pre-commit-config.yaml << EOF
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint-docker
EOF
```

---

## IV. Environment-Specific Testing

### A. Matrix Testing Locally

**Problem:** CI tests multiple Python/Node versions - hard to replicate locally.

**Solution:** Use `tox` (Python) or `nvm` (Node.js).

#### Python - tox

```bash
# Install tox
pip install tox

# Create tox.ini
cat > tox.ini << EOF
[tox]
envlist = py38,py39,py310,py311,py312

[testenv]
deps =
    pytest
    pytest-cov
commands =
    pytest tests/ --cov=src

[testenv:lint]
deps =
    flake8
    black
    mypy
commands =
    flake8 src/ tests/
    black --check src/ tests/
    mypy src/

[testenv:security]
deps =
    bandit
    pip-audit
commands =
    bandit -r src/
    pip-audit
EOF

# Run all environments
tox

# Run specific environment
tox -e py311

# Run in parallel
tox -p auto

# Recreate environments (after dependency changes)
tox -r
```

#### Node.js - nvm

```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Test multiple Node versions
for version in 16 18 20; do
    echo "Testing Node $version..."
    nvm use $version
    npm ci
    npm test
done

# Or use Docker
docker run -v $(pwd):/app node:16 npm test
docker run -v $(pwd):/app node:18 npm test
docker run -v $(pwd):/app node:20 npm test
```

### B. OS-Specific Testing

**Problem:** CI tests on Linux/macOS/Windows - you only have one OS.

**Solution:** Use Docker or VMs.

```bash
# Test on different OS using Docker
# Ubuntu
docker run -v $(pwd):/workspace -w /workspace ubuntu:22.04 /bin/bash -c "
    apt-get update && 
    apt-get install -y python3 python3-pip && 
    pip3 install -r requirements.txt && 
    pytest tests/
"

# Alpine (smaller, faster)
docker run -v $(pwd):/workspace -w /workspace python:3.11-alpine sh -c "
    pip install -r requirements.txt && 
    pytest tests/
"

# Windows (via Wine or Windows Container)
# Requires Docker Desktop with Windows containers enabled
docker run -v $(pwd):C:\workspace -w C:\workspace mcr.microsoft.com/windows/servercore:ltsc2022
```

---

## V. Dependency Management Checks

### A. Dependency Resolution Verification

**Problem:** CI fails with "dependency conflict" errors.

**Solution:** Verify dependency resolution locally.

```bash
# Python - check for conflicts
pip install pip-tools
pip-compile --resolver=backtracking requirements.in

# Check if requirements.txt is up to date
pip-compile --dry-run requirements.in

# Verify no conflicts
pip install -r requirements.txt --dry-run

# Check for security issues
pip install pip-audit
pip-audit

# Node.js - check for conflicts
npm ci --dry-run

# Check for outdated dependencies
npm outdated

# Check for security issues
npm audit

# Fix automatically
npm audit fix
```

### B. Lock File Validation

```bash
# Python - Verify lock file is up to date
# Using Poetry
poetry check

# Using Pipenv
pipenv verify

# Using uv
uv pip compile requirements.in --output-file requirements.txt
diff requirements.txt <(uv pip compile requirements.in)

# Node.js - Verify package-lock.json
npm ci  # Fails if package-lock.json is out of sync

# Yarn
yarn install --frozen-lockfile
```

---

## VI. Fast Feedback Scripts

### A. CI Simulation Script

Create a script that mimics your CI pipeline:

```bash
#!/bin/bash
# ci-local.sh - Run CI checks locally

set -e  # Exit on first error

echo "🚀 Running local CI simulation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function success() {
    echo -e "${GREEN}✓${NC} $1"
}

function error() {
    echo -e "${RED}✗${NC} $1"
}

function warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Step 1: Environment check
echo "→ Checking environment..."
if ! command -v python &> /dev/null; then
    error "Python not found"
    exit 1
fi
success "Environment OK"

# Step 2: Install dependencies
echo "→ Installing dependencies..."
if ! pip install -q -r requirements.txt; then
    error "Dependency installation failed"
    exit 1
fi
success "Dependencies installed"

# Step 3: Code formatting
echo "→ Checking code formatting..."
if ! black --check .; then
    error "Code formatting issues found"
    warning "Run: black ."
    exit 1
fi
success "Code formatting OK"

# Step 4: Linting
echo "→ Running linter..."
if ! flake8 src/ tests/; then
    error "Linting failed"
    exit 1
fi
success "Linting OK"

# Step 5: Type checking
echo "→ Running type checks..."
if ! mypy src/; then
    error "Type checking failed"
    exit 1
fi
success "Type checking OK"

# Step 6: Security scanning
echo "→ Running security scan..."
if ! bandit -r src/ -q; then
    warning "Security issues found"
else
    success "Security scan OK"
fi

# Step 7: Tests
echo "→ Running tests..."
if ! pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80; then
    error "Tests failed"
    exit 1
fi
success "Tests passed"

# Step 8: Build check
echo "→ Checking build..."
if [ -f "setup.py" ]; then
    if ! python setup.py build > /dev/null 2>&1; then
        error "Build failed"
        exit 1
    fi
fi
success "Build OK"

# Step 9: Docker build (if Dockerfile exists)
if [ -f "Dockerfile" ]; then
    echo "→ Testing Docker build..."
    if ! docker build -t test-build . > /dev/null 2>&1; then
        error "Docker build failed"
        exit 1
    fi
    success "Docker build OK"
fi

echo ""
echo -e "${GREEN}✅ All CI checks passed!${NC}"
echo "Safe to push to GitHub."
```

Make it executable and run:

```bash
chmod +x ci-local.sh
./ci-local.sh
```

### B. Quick Check Script (Fast Subset)

For rapid iteration during development:

```bash
#!/bin/bash
# quick-check.sh - Fast subset of CI checks

set -e

echo "⚡ Running quick checks..."

# Just the essentials
black --check src/ tests/ || (echo "Run: black ." && exit 1)
flake8 src/ tests/ --select=E9,F63,F7,F82  # Only critical errors
pytest tests/ -x -v  # Stop on first failure

echo "✅ Quick checks passed!"
```

---

## VII. Common CI/CD Issues & Local Detection

### A. Import Errors

**Issue:** Code works locally but fails on CI with "ModuleNotFoundError".

**Cause:** Missing dependency in requirements.txt, circular imports, incorrect PYTHONPATH.

**Local Detection:**

```bash
# Fresh environment test
python -m venv test_env
source test_env/bin/activate
pip install -r requirements.txt
python -m pytest tests/  # Will fail if imports broken

# OR use tox (recommended)
tox -e py311 --recreate

# Check for circular imports
pydeps src/ --show-cycles
```

### B. Environment Variables

**Issue:** Tests pass locally but fail on CI with "KeyError" or missing config.

**Cause:** Relying on .env file that's gitignored.

**Local Detection:**

```bash
# Run tests without .env loaded
env -i $(which python) -m pytest tests/

# OR use .env.example as test baseline
cp .env.example .env.test
export $(cat .env.test | xargs)
pytest tests/

# Validate required env vars
cat > check-env.sh << 'EOF'
#!/bin/bash
required_vars=(
    "DATABASE_URL"
    "API_KEY"
    "SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Missing required env var: $var"
        exit 1
    fi
done
EOF
```

### C. File Path Issues

**Issue:** Hardcoded paths fail on different OS.

**Cause:** Using `\` on Windows, `/` on Unix.

**Local Detection:**

```bash
# Search for hardcoded paths
grep -r "C:\\" src/
grep -r "/home/" src/
grep -r "\\Users\\" src/

# Use pathlib instead
# Bad:  path = "src/utils.py"
# Good: from pathlib import Path; path = Path("src") / "utils.py"
```

### D. Line Ending Issues

**Issue:** CI fails with parsing errors on Windows.

**Cause:** CRLF vs LF line endings.

**Local Detection:**

```bash
# Check line endings
file script.sh
# Should show: "ASCII text" not "ASCII text, with CRLF line terminators"

# Fix globally
git config --global core.autocrlf input  # Convert CRLF to LF on commit

# Fix locally
dos2unix script.sh

# Add to .gitattributes
cat >> .gitattributes << EOF
* text=auto
*.sh text eol=lf
*.py text eol=lf
EOF
```

---

## VIII. Integration with Agent Harness

If using the agent harness from earlier, add CI checking:

```python
# In your harness configuration

class CICheckTool:
    """Tool for running CI checks before committing."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
    
    def run_ci_checks(self) -> dict[str, bool]:
        """Run all CI checks locally."""
        results = {}
        
        # Formatting
        results["formatting"] = self._check_formatting()
        
        # Linting
        results["linting"] = self._check_linting()
        
        # Tests
        results["tests"] = self._run_tests()
        
        # Build
        results["build"] = self._check_build()
        
        return results
    
    def _check_formatting(self) -> bool:
        """Check code formatting."""
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=self.project_path,
            capture_output=True
        )
        return result.returncode == 0
    
    def _check_linting(self) -> bool:
        """Run linter."""
        result = subprocess.run(
            ["flake8", "src/", "tests/"],
            cwd=self.project_path,
            capture_output=True
        )
        return result.returncode == 0
    
    def _run_tests(self) -> bool:
        """Run test suite."""
        result = subprocess.run(
            ["pytest", "tests/", "-q"],
            cwd=self.project_path,
            capture_output=True
        )
        return result.returncode == 0
    
    def _check_build(self) -> bool:
        """Check if project builds."""
        if (self.project_path / "setup.py").exists():
            result = subprocess.run(
                ["python", "setup.py", "build"],
                cwd=self.project_path,
                capture_output=True
            )
            return result.returncode == 0
        return True

# Register with harness
registry.register("ci_check", CICheckTool(project_path=".").run_ci_checks)
```

Then in your agent instructions:

```markdown
## Pre-Commit Protocol

Before committing ANY code changes, you MUST:

1. Run CI checks locally: `ci_check()`
2. If any check fails, fix the issue before committing
3. Do NOT commit if CI checks would fail on GitHub

Example workflow:
1. Make code changes
2. Run: ci_check()
3. Review results
4. Fix any failures
5. Commit only when all checks pass
```

---

## IX. Tools Summary & Quick Reference

| Tool | Purpose | Install | Usage |
|------|---------|---------|-------|
| **pre-commit** | Git hook framework | `pip install pre-commit` | `pre-commit install` |
| **act** | Run GitHub Actions locally | `brew install act` | `act -j test` |
| **actionlint** | Validate GitHub Actions YAML | `brew install actionlint` | `actionlint .github/workflows/*.yml` |
| **yamllint** | Validate YAML syntax | `pip install yamllint` | `yamllint .github/workflows/*.yml` |
| **hadolint** | Dockerfile linter | `brew install hadolint` | `hadolint Dockerfile` |
| **tox** | Multi-env Python testing | `pip install tox` | `tox` |
| **pip-audit** | Security vulnerability scan | `pip install pip-audit` | `pip-audit` |
| **mypy** | Type checking | `pip install mypy` | `mypy src/` |
| **black** | Code formatting | `pip install black` | `black --check .` |
| **flake8** | Linting | `pip install flake8` | `flake8 src/` |

---

## X. Complete Setup Checklist

### Phase 1: Basic Hooks (15 minutes)
- [ ] Install pre-commit framework
- [ ] Create .pre-commit-config.yaml
- [ ] Run `pre-commit install`
- [ ] Create pre-push hook script
- [ ] Test hooks with dummy commit

### Phase 2: CI Simulation (30 minutes)
- [ ] Install `act` for GitHub Actions
- [ ] Test running workflows locally
- [ ] Create ci-local.sh script
- [ ] Add Docker validation (if applicable)

### Phase 3: Validation Tools (20 minutes)
- [ ] Install actionlint
- [ ] Install yamllint
- [ ] Install hadolint (if using Docker)
- [ ] Add all to pre-commit config

### Phase 4: Environment Testing (30 minutes)
- [ ] Install tox (Python) or nvm (Node)
- [ ] Create tox.ini or test script
- [ ] Test multiple Python/Node versions
- [ ] Document matrix testing process

### Phase 5: Quick Feedback (15 minutes)
- [ ] Create quick-check.sh script
- [ ] Add to IDE/editor shortcuts
- [ ] Document for team

---

## XI. Best Practices

1. **Run quick-check.sh frequently** (every 15-30 min during dev)
2. **Run ci-local.sh before pushing** (always)
3. **Use act for complex workflow changes** (whenever modifying .github/workflows/)
4. **Keep pre-commit hooks fast** (<10 seconds total)
5. **Run full CI simulation nightly** (via cron or scheduled task)
6. **Update tools regularly** (monthly: `pre-commit autoupdate`)
7. **Share scripts with team** (commit them to repo)
8. **Document exceptions** (when you override a check, note why)

---

## XII. Time Savings Estimate

**Before (no local checks):**
- Push → wait 5 min → CI fails → fix → push → wait 5 min → repeat
- Average: 3 cycles × 10 min = 30 minutes per feature

**After (local checks):**
- Run quick-check (1 min) → fix → run ci-local (3 min) → push → CI passes
- Average: 4 minutes per feature

**Savings: 26 minutes per feature = ~87% reduction in CI wait time**

Plus:
- Fewer embarassing broken builds
- Less context switching
- Lower CI/CD resource usage
- Faster iteration during development

---

## Summary

**Top 3 Most Impactful:**

1. **Pre-push hook with full CI checks** - Catches 90% of issues
2. **act for GitHub Actions** - Tests exact CI environment
3. **ci-local.sh script** - One command for comprehensive check

**Quick Start (5 minutes):**

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Create basic pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
set -e
pytest tests/
black --check .
flake8 .
EOF
chmod +x .git/hooks/pre-push

# Done! Now git push will run checks first.
```

Start simple, add complexity as needed. The goal is **fast local feedback**, not perfect coverage.
