#!/bin/bash
# Status dashboard (agent-6x9.5)
# Shows comprehensive status of cleanup enforcement

echo "📊 Cleanup Enforcement Status Dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# System status
echo "🔧 System Components:"
echo ""

# Hooks
if [ -f .git/hooks/pre-commit ] && [ -x .git/hooks/pre-commit ]; then
    echo "  ✅ Pre-commit hook installed"
else
    echo "  ❌ Pre-commit hook missing"
    echo "     Install: bash .harness/install_hooks.sh"
fi

# CI workflow
if [ -f .github/workflows/cleanup-validation.yml ] || [ -d .github/workflows ]; then
    echo "  ✅ CI validation workflow present"
else
    echo "  ⚠️  CI validation not found"
fi

# Session tracker
if python3 -c "import sys; sys.path.insert(0, 'src'); from agent_harness.session_tracker import SessionTracker" 2>/dev/null; then
    echo "  ✅ SessionTracker available"
else
    echo "  ❌ SessionTracker not available"
fi

# Worktree manager
if python3 -c "import sys; sys.path.insert(0, 'src'); from agent_harness.git_worktree_manager import GitWorktreeManager" 2>/dev/null; then
    echo "  ✅ GitWorktreeManager available"
else
    echo "  ⚠️  GitWorktreeManager not available (optional)"
fi

echo ""
echo "📋 Current Workspace:"
echo ""

# Session status
if [ -f .agent/sessions/session.lock ]; then
    echo "  📍 Active session detected"
    echo "     Run: python check_protocol_compliance.py --status"
else
    echo "  ⭕ No active session"
fi

echo ""

# Cleanup status
if bash .harness/scripts/validate-cleanup.sh > /dev/null 2>&1; then
    echo "  ✅ Workspace clean (0 violations)"
else
    VIOLATIONS=$(bash .harness/scripts/validate-cleanup.sh 2>&1 | grep "^  -" | wc -l || echo "0")
    echo "  ⚠️  $VIOLATIONS cleanup violation(s)"
    echo "     Fix: bash .harness/scripts/auto-cleanup.sh"
fi

# Worktrees
WORKTREES=$(($(git worktree list 2>/dev/null | wc -l) - 1))
if [ "$WORKTREES" -eq 0 ]; then
    echo "  ✅ No active worktrees"
elif [ "$WORKTREES" -gt 0 ]; then
    echo "  ⚠️  $WORKTREES active worktree(s)"
    echo "     Manage: bash .harness/scripts/cleanup-worktrees.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Quick Commands:"
echo "  validate-cleanup.sh      - Check for violations"
echo "  auto-cleanup.sh          - Auto-remove violations"
echo "  pre-pr-checklist.sh     - Pre-PR validation"
echo "  cleanup-worktrees.sh    - Manage worktrees"
echo "  status-dashboard.sh     - This dashboard"
echo ""
