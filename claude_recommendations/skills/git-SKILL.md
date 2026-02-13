---
name: git
description: Comprehensive Git workflow guidance for agents including commits, branches, merges, rebases, and conflict resolution. Ensures clean history and proper version control practices.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# 🔀 Git Skill

**Purpose**: Guide agents through Git operations with best practices for commits, branching, merging, and conflict resolution.

## 🎯 Mission

- Write clear, atomic commits with proper messages
- Manage branches effectively (feature/bugfix/hotfix)
- Handle merge conflicts systematically
- Maintain clean, linear Git history
- Use Git commands safely and correctly

## 📋 When to Use This Skill

Use this skill when:
- Starting new work (creating branches)
- Committing changes (writing commit messages)
- Merging or rebasing branches
- Resolving merge conflicts
- Cleaning up Git history
- Understanding repository state

## 🔄 Git Workflow Patterns

### Pattern 1: Feature Development

```bash
# 1. Start from clean main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/add-user-auth

# 3. Work and commit atomically
# ... make changes ...
git add -p  # Stage changes interactively (review each hunk)
git commit -m "feat: add JWT token generation"

# ... more changes ...
git add src/auth/login.py tests/test_login.py
git commit -m "feat: implement login endpoint"

# 4. Before merging: rebase on latest main
git fetch origin main
git rebase origin/main

# 5. Push and create PR
git push origin feature/add-user-auth
```

### Pattern 2: Bug Fix

```bash
# 1. Create bugfix branch from main
git checkout main
git pull origin main
git checkout -b bugfix/fix-memory-leak

# 2. Fix and commit
# ... make fix ...
git add src/parser.py
git commit -m "fix: resolve memory leak in parser

- Close file handles properly
- Add context manager for resource cleanup
- Add regression test

Fixes #234"

# 3. Push
git push origin bugfix/fix-memory-leak
```

### Pattern 3: Hotfix (Production)

```bash
# 1. Branch from production tag
git checkout -b hotfix/critical-security-fix v1.2.3

# 2. Make minimal fix
git add src/security/validator.py
git commit -m "security: patch SQL injection vulnerability

CRITICAL: Validate all user inputs before queries

CVE-2024-XXXXX"

# 3. Push and deploy immediately
git push origin hotfix/critical-security-fix
```

## ✍️ Commit Message Guidelines

### Format: Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting, missing semicolons, etc.
- **refactor**: Code restructuring without behavior change
- **perf**: Performance improvement
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **revert**: Reverting a previous commit

### Examples

#### ✅ Good Commit Messages

```bash
# Feature with context
git commit -m "feat(auth): add JWT token refresh mechanism

- Implement refresh token endpoint
- Add token expiration checking
- Update authentication middleware
- Add comprehensive tests for token lifecycle

Closes #123"

# Bug fix with reproduction steps
git commit -m "fix(parser): handle empty input gracefully

Previously crashed with IndexError on empty strings.
Now returns None with appropriate logging.

Fixes #456"

# Performance improvement with metrics
git commit -m "perf(database): optimize user query performance

- Add index on email column
- Implement query result caching
- Reduce N+1 queries in user lookup

Results: 85% reduction in query time (320ms → 48ms)"
```

#### ❌ Bad Commit Messages

```bash
# Too vague
git commit -m "fix bug"
git commit -m "update code"
git commit -m "changes"

# No context
git commit -m "fix parser"  # What was broken? How fixed?

# Multiple unrelated changes
git commit -m "fix parser, update docs, refactor tests"  # Should be 3 commits
```

## 🌿 Branch Management

### Branch Naming Conventions

```bash
# Feature branches
feature/add-user-authentication
feature/implement-caching
feature/user-dashboard

# Bug fix branches
bugfix/fix-login-error
bugfix/resolve-memory-leak
bugfix/correct-timezone-handling

# Hotfix branches (for production)
hotfix/patch-security-vulnerability
hotfix/fix-payment-processing

# Experimental/spike branches
spike/explore-graphql
experiment/new-architecture
```

### Branch Lifecycle

```bash
# Create and switch
git checkout -b feature/my-feature

# List branches
git branch -a  # All branches (local + remote)
git branch -vv # With tracking info

# Delete merged branch (local)
git branch -d feature/my-feature

# Delete unmerged branch (force)
git branch -D feature/abandoned-work

# Delete remote branch
git push origin --delete feature/my-feature

# Prune deleted remote branches
git fetch --prune
```

### Keep Branches Updated

```bash
# Option 1: Rebase (recommended - clean history)
git checkout feature/my-feature
git fetch origin main
git rebase origin/main

# Option 2: Merge (preserves branch structure)
git checkout feature/my-feature
git merge origin/main
```

## 🔀 Merging Strategies

### Fast-Forward Merge (Simple)

```bash
# When feature branch is ahead of main
git checkout main
git merge feature/simple-change  # Fast-forward automatically
```

### No-Fast-Forward Merge (Preserve Branch History)

```bash
# Preserve that a feature branch existed
git checkout main
git merge --no-ff feature/my-feature -m "Merge feature: add user auth"
```

### Squash Merge (Clean History)

```bash
# Combine all feature commits into one
git checkout main
git merge --squash feature/my-feature
git commit -m "feat: add complete user authentication system

- JWT token generation and validation
- Login/logout endpoints
- Session management
- Comprehensive test coverage

Closes #123"
```

## 🔄 Rebasing

### Interactive Rebase (Clean Up Commits)

```bash
# Rebase last 3 commits
git rebase -i HEAD~3

# In editor, you can:
# pick - keep commit as-is
# reword - change commit message
# squash - combine with previous commit
# fixup - like squash but discard commit message
# drop - remove commit

# Example:
pick abc123 feat: add login
squash def456 fix typo in login  # Combine into previous commit
reword ghi789 feat: add logout   # Change message
drop jkl012 wip: debugging        # Remove this commit
```

### Common Rebase Scenarios

```bash
# Update feature branch with latest main
git checkout feature/my-feature
git rebase origin/main

# Rebase onto different base
git rebase --onto new-base old-base feature-branch

# Abort if things go wrong
git rebase --abort

# Continue after resolving conflicts
git rebase --continue
```

## ⚔️ Merge Conflict Resolution

### Understanding Conflicts

```bash
# When you see conflicts:
git status

# Shows:
# both modified: src/file.py
```

### Conflict Markers

```python
<<<<<<< HEAD (current branch)
def process_data(data):
    return data.upper()
=======
def process_data(data):
    return data.lower()
>>>>>>> feature/my-branch
```

### Resolution Steps

```bash
# 1. Identify conflicted files
git status

# 2. Open each file and resolve conflicts
# - Remove conflict markers (<<<<<<<, =======, >>>>>>>)
# - Choose correct code or combine both versions
# - Test that resolution works

# 3. Stage resolved files
git add src/file.py

# 4. Continue merge/rebase
git rebase --continue  # If rebasing
git merge --continue   # If merging

# Or commit if merging manually
git commit -m "Merge feature/my-branch into main"
```

### Conflict Resolution Tools

```bash
# Use merge tool (visual)
git mergetool

# See what changed in both branches
git diff HEAD...MERGE_HEAD

# Accept one side completely
git checkout --ours src/file.py    # Keep your version
git checkout --theirs src/file.py  # Keep their version
git add src/file.py
```

### Common Conflict Patterns

**Pattern 1: Same Function Modified**
```python
# Resolution: Combine both changes intelligently
<<<<<<< HEAD
def calculate(x, y):
    result = x + y  # Addition
    return result
=======
def calculate(x, y):
    result = x * y  # Multiplication
    return result
>>>>>>> feature/calculator

# Resolved: Support both operations
def calculate(x, y, operation='add'):
    if operation == 'add':
        result = x + y
    elif operation == 'multiply':
        result = x * y
    return result
```

**Pattern 2: Import Order Conflicts**
```python
# Resolution: Combine and sort alphabetically
<<<<<<< HEAD
import json
import requests
=======
import os
import sys
>>>>>>> feature/utils

# Resolved:
import json
import os
import requests
import sys
```

## 🔍 Checking Repository State

### Status and Diff

```bash
# What changed?
git status

# See unstaged changes
git diff

# See staged changes
git diff --cached

# See changes between branches
git diff main..feature/my-branch

# See changes in specific file
git diff src/file.py

# See word-level diff (better for text)
git diff --word-diff
```

### History and Logs

```bash
# View commit history
git log

# Compact one-line view
git log --oneline

# Visual graph
git log --oneline --graph --all

# Last N commits
git log -10

# Commits by author
git log --author="Agent Name"

# Commits affecting specific file
git log -- src/file.py

# Search commits by message
git log --grep="fix bug"
```

## 🔙 Undoing Changes

### Unstage Files

```bash
# Unstage specific file
git restore --staged src/file.py

# Unstage all files
git restore --staged .
```

### Discard Uncommitted Changes

```bash
# Discard changes in specific file
git restore src/file.py

# Discard all changes (DANGEROUS)
git restore .
```

### Undo Last Commit

```bash
# Keep changes (soft reset)
git reset --soft HEAD~1

# Keep changes but unstaged (mixed reset)
git reset HEAD~1

# Discard changes completely (DANGEROUS)
git reset --hard HEAD~1
```

### Revert Commit (Safe)

```bash
# Create new commit that undoes previous commit
git revert abc123

# Revert multiple commits
git revert abc123..def456
```

## 🧹 Keeping History Clean

### Before Pushing

```bash
# Squash work-in-progress commits
git rebase -i HEAD~5

# In editor:
pick abc123 feat: start feature
squash def456 wip: continue
squash ghi789 wip: almost done
squash jkl012 wip: debugging
pick mno345 feat: finalize feature
# Results in 2 clean commits
```

### Amend Last Commit

```bash
# Add forgotten changes to last commit
git add forgotten_file.py
git commit --amend --no-edit

# Change last commit message
git commit --amend -m "Better commit message"
```

## 🚫 What NOT to Do

### ❌ Don't Commit These

```bash
# Secrets and credentials
.env
config/secrets.yaml
*.pem
*.key

# Large binary files
*.mp4
*.zip (large)
database_dump.sql

# Generated files
__pycache__/
*.pyc
node_modules/
dist/
build/

# IDE files
.vscode/
.idea/
*.swp
```

Use `.gitignore`:

```bash
# .gitignore example
__pycache__/
*.pyc
.env
*.log
node_modules/
dist/
.DS_Store
```

### ❌ Don't Do These Actions

```bash
# DON'T force push to shared branches
git push --force origin main  # ❌ NEVER

# DON'T commit unrelated changes together
git add .
git commit -m "various fixes"  # ❌ Not atomic

# DON'T use vague commit messages
git commit -m "fix"  # ❌ What was fixed?
git commit -m "update"  # ❌ What was updated?

# DON'T rewrite published history
git push --force  # ❌ Unless you know what you're doing
```

## ✅ Best Practices Checklist

Before committing:
- [ ] Changes are atomic (one logical change)
- [ ] Commit message is clear and descriptive
- [ ] Code is tested (if applicable)
- [ ] No secrets or large files included
- [ ] `.gitignore` is properly configured
- [ ] Changes are staged selectively (`git add -p`)

Before pushing:
- [ ] Commits are clean (no "wip" commits)
- [ ] History is linear (rebased if needed)
- [ ] All tests pass
- [ ] Branch is up-to-date with main

Before merging:
- [ ] Code review completed (if applicable)
- [ ] CI/CD passes
- [ ] Conflicts resolved
- [ ] Target branch is correct

## 🛠️ Useful Git Commands

### Information

```bash
# Who changed this line?
git blame src/file.py

# When was this file last changed?
git log -1 -- src/file.py

# What changed in commit abc123?
git show abc123

# Is commit abc123 in this branch?
git branch --contains abc123
```

### Stashing

```bash
# Save work-in-progress
git stash

# Save with message
git stash save "work in progress on feature"

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{2}

# Drop stash
git stash drop stash@{0}
```

### Reflog (Recover Lost Commits)

```bash
# Show all ref changes
git reflog

# Recover from mistake
git reflog  # Find the commit hash before mistake
git reset --hard abc123  # Go back to that state
```

## 🔗 Integration with Other Skills

- **TDD Skill**: Commit after red/green/refactor phases
- **Code Review Skill**: Clean commits make reviews easier
- **Finalization Skill**: Ensure clean git state before finalizing
- **Orchestrator**: Git status checked during initialization

## 📚 Common Scenarios

### Scenario 1: Made Commit on Wrong Branch

```bash
# You committed to main instead of feature branch
git branch feature/my-work  # Create branch with current commits
git reset --hard origin/main  # Reset main to match remote
git checkout feature/my-work  # Switch to new branch
```

### Scenario 2: Need to Split One Commit into Multiple

```bash
# Reset but keep changes
git reset HEAD~1

# Stage and commit separately
git add src/auth.py
git commit -m "feat: add authentication"

git add src/validation.py
git commit -m "feat: add input validation"
```

### Scenario 3: Accidentally Committed Secret

```bash
# Remove file from history (REWRITE HISTORY - dangerous)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch path/to/secret.env' \
  --prune-empty --tag-name-filter cat -- --all

# Or use BFG Repo-Cleaner (faster)
bfg --delete-files secret.env

# Then force push (coordinate with team!)
git push origin --force --all
```

## 🆘 Emergency Recovery

### Lost Work After Reset

```bash
# Find the lost commit
git reflog

# Recover it
git cherry-pick abc123  # Apply that commit
# or
git reset --hard abc123  # Go back to that state
```

### Broken Rebase

```bash
# Abort and start over
git rebase --abort

# Or fix and continue
# ... resolve conflicts ...
git add .
git rebase --continue
```

### Corrupted Repository

```bash
# Try git fsck
git fsck --full

# Clone fresh copy and apply changes manually
git clone <repository-url> fresh-copy
# Copy your work to fresh clone
```

---

**Remember**: Git is powerful but can be dangerous. When in doubt:
1. Check `git status` frequently
2. Commit often (can always squash later)
3. Make backups of important work
4. Ask for help before force-pushing
5. Use `git reflog` to recover from mistakes
