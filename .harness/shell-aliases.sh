# Shell aliases for cleanup enforcement (agent-6x9.5)
# Add to your ~/.bashrc or ~/.zshrc:
#   source /path/to/.harness/shell-aliases.sh

# Quick validation
alias cleanup-check='bash .harness/scripts/validate-cleanup.sh'

# Auto cleanup
alias cleanup-fix='bash .harness/scripts/auto-cleanup.sh'

# Status dashboard
alias cleanup-status='bash .harness/scripts/status-dashboard.sh'

# Pre-PR check
alias pre-pr='bash .harness/scripts/pre-pr-checklist.sh'

# Session management
alias session-init='python check_protocol_compliance.py --init'
alias session-status='python check_protocol_compliance.py --status'
alias session-close='python check_protocol_compliance.py --close'

# Worktree management
alias worktree-cleanup='bash .harness/scripts/cleanup-worktrees.sh'

echo "💡 Cleanup enforcement aliases loaded"
echo "   cleanup-check, cleanup-fix, cleanup-status, pre-pr"
echo "   session-init, session-status, session-close"
