#!/bin/bash
# ci-local.sh - Run CI checks locally

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

function info() {
    echo -e "${BLUE}i${NC} $1"
}

echo -e "🚀 ${BLUE}Running local CI simulation...${NC}"
echo "========================================="

# Step 1: Environment check
info "Checking environment (uv)..."
if ! command -v uv &> /dev/null; then
    error "uv not found. Please install uv (https://github.com/astral-sh/uv)."
    exit 1
fi
success "Environment OK"

# Step 2: Code formatting
info "Checking code formatting (ruff format)..."
if ! uv run ruff format --check .; then
    error "Code formatting issues found"
    warning "Run: uv run ruff format ."
    exit 1
fi
success "Code formatting OK"

# Step 3: Linting
info "Running linter (ruff check)..."
if ! uv run ruff check .; then
    error "Linting failed"
    warning "Run: uv run ruff check --fix ."
    exit 1
fi
success "Linting OK"

# Step 4: Security scanning
info "Running security scan (bandit)..."
if ! uv run bandit -qc pyproject.toml -r src/; then
    error "Security issues found"
    exit 1
fi
success "Security scan OK"

# Step 5: Tests
info "Running tests (pytest)..."
if ! uv run pytest -v; then
    error "Tests failed"
    exit 1
fi
success "Tests passed"

# Step 6: Beads check (No blockers)
info "Checking Beads for blockers..."
# if bd ready returns non-empty output with blockers, we might want to warn or fail
# For now, just show the status
bd ready
success "Beads check complete"

echo "========================================="
echo -e "${GREEN}✅ All local CI checks passed!${NC}"
echo "Safe to push to GitHub."
