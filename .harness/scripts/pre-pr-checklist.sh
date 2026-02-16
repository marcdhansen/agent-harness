#!/bin/bash
# Pre-PR checklist (agent-6x9.5)
# Comprehensive checks before creating PR

set -e

echo "✅ Pre-PR Checklist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_SKIPPED=0

# Check 1: Cleanup validation
echo "1. Cleanup Validation"
if bash .harness/scripts/validate-cleanup.sh > /dev/null 2>&1; then
    echo "   ✅ No cleanup violations"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "   ❌ Cleanup violations found"
    echo "      Run: bash .harness/scripts/auto-cleanup.sh"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
fi

# Check 2: No active session
echo "2. Session Status"
if [ -f .agent/sessions/session.lock ]; then
    echo "   ❌ Active session found"
    echo "      Run: python check_protocol_compliance.py --close"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
else
    echo "   ✅ No active session"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
fi

# Check 3: Git status
echo "3. Git Status"
if [ -z "$(git status --porcelain)" ]; then
    echo "   ✅ Working tree clean"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "   ⚠️  Uncommitted changes"
    echo "      Review: git status"
    # Not a failure - might be intentional for staged changes
fi

# Check 4: Worktrees
echo "4. Git Worktrees"
WORKTREES=$(git worktree list | wc -l)
if [ "$WORKTREES" -eq 1 ]; then
    echo "   ✅ No active worktrees"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
else
    echo "   ⚠️  $((WORKTREES - 1)) active worktree(s)"
    echo "      Run: bash .harness/scripts/cleanup-worktrees.sh"
fi

# Check 5: Tests (if available)
echo "5. Tests"
if [ -f "pytest.ini" ] || [ -d "tests/" ]; then
    if python3 -m pytest tests/ -q --tb=no > /dev/null 2>&1; then
        echo "   ✅ Tests passing"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "   ❌ Tests failing"
        echo "      Run: pytest tests/"
        CHECKS_FAILED=$((CHECKS_FAILED + 1))
    fi
else
    echo "   ⏭️  No tests found"
    CHECKS_SKIPPED=$((CHECKS_SKIPPED + 1))
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary: $CHECKS_PASSED passed, $CHECKS_FAILED failed, $CHECKS_SKIPPED skipped"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo "✅ Ready to create PR!"
    exit 0
else
    echo "❌ Fix issues before creating PR"
    exit 1
fi
