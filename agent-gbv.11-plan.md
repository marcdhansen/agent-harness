# Implementation Plan - Local CI/CD Simulation (agent-gbv.11)

## Problem

CI/CD failures on GitHub Actions are slow to debug and waste resources. Currently, there is no single command to run all checks (linting, formatting, security, tests) locally in a way that ensures compliance with the CI/CD pipeline.

## Proposed Changes

### 1. Create Local CI Script (`scripts/ci-local.sh`)

Implement a comprehensive shell script that runs all necessary checks:

- **Environment Check**: Ensure dependencies are installed.
- **Linting & Formatting**: Run `ruff check` and `ruff format --check`.
- **Security Audit**: Run `bandit`.
- **Unit & Integration Tests**: Run `pytest`.
- **Beads Checks**: Run `bd ready` to ensure no blockers.

### 2. Update Documentation

- Add instructions to `README.md` on how to use the local CI script.
- Ensure the script is easy to call during development.

### 3. Verification Plan

#### Automated Verification

- Run `./scripts/ci-local.sh` and ensure it correctly identifies both passing and failing states.
- Mock a linting error and verify the script fails.
- Mock a test failure and verify the script fails.

#### Manual Verification

- Verify that passing the local CI script results in a successful GitHub Actions run.

## Tasks

- [ ] Create `scripts/ci-local.sh`
- [ ] Add execution permissions
- [ ] Test with current codebase
- [ ] Update README or contribute to "Quick Start"
