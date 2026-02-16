#!/bin/bash
# Cleanup orphaned git worktrees (agent-6x9.4)

set -e

# Parse arguments
FORCE_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes|--force)
            FORCE_MODE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-y|--yes|--force]"
            echo "  -y, --yes, --force  Skip confirmation prompt (for agents/CI)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check environment variable for agent mode
if [ "${HARNESS_WORKTREE_CLEANUP:-}" = "true" ] || [ "${HARNESS_WORKTREE_CLEANUP:-}" = "1" ]; then
    FORCE_MODE=true
fi

echo "🧹 Git Worktree Cleanup Utility"
echo ""

# Check if in git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# List all worktrees
echo "📋 Active worktrees:"
git worktree list
echo ""

# Prune invalid references
echo "🔍 Pruning invalid worktree references..."
git worktree prune --verbose
echo ""

# Find potential orphans
echo "🔍 Checking for orphaned worktrees..."
WORKTREES=$(git worktree list --porcelain | grep "^worktree " | cut -d' ' -f2-)
MAIN_WORKTREE=$(git rev-parse --show-toplevel)

ORPHANED=()
for wt in $WORKTREES; do
    # Skip main worktree
    if [ "$wt" = "$MAIN_WORKTREE" ]; then
        continue
    fi
    
    # Check if directory exists
    if [ ! -d "$wt" ]; then
        ORPHANED+=("$wt")
        continue
    fi
    
    # Check if old (no activity in 24h)
    if [ -d "$wt" ]; then
        LAST_MODIFIED=$(find "$wt" -type f -mmin -1440 2>/dev/null | wc -l)
        if [ "$LAST_MODIFIED" -eq 0 ]; then
            # Check if clean
            cd "$wt"
            if [ -z "$(git status --porcelain)" ]; then
                ORPHANED+=("$wt")
            fi
            cd - > /dev/null
        fi
    fi
done

# Report orphans
if [ ${#ORPHANED[@]} -eq 0 ]; then
    echo "✅ No orphaned worktrees found"
    exit 0
fi

echo "⚠️  Found ${#ORPHANED[@]} potentially orphaned worktree(s):"
for wt in "${ORPHANED[@]}"; do
    echo "  - $wt"
done
echo ""

# Agent/CI mode: skip confirmation
if [ "$FORCE_MODE" = true ]; then
    echo "🤖 Agent/CI mode: Removing orphaned worktrees (--yes flag detected)"
    for wt in "${ORPHANED[@]}"; do
        echo "Removing: $wt"
        git worktree remove "$wt" --force 2>/dev/null || true
    done
    echo "✅ Cleanup complete"
elif [ -t 0 ]; then
    read -p "Remove these worktrees? [y/N]: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for wt in "${ORPHANED[@]}"; do
            echo "Removing: $wt"
            git worktree remove "$wt" --force 2>/dev/null || true
        done
        echo "✅ Cleanup complete"
    else
        echo "Cleanup cancelled"
    fi
else
    # Non-interactive but not forced - ask anyway
    read -p "Remove these worktrees? [y/N]: " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for wt in "${ORPHANED[@]}"; do
            echo "Removing: $wt"
            git worktree remove "$wt" --force 2>/dev/null || true
        done
        echo "✅ Cleanup complete"
    else
        echo "Cleanup cancelled"
    fi
fi
