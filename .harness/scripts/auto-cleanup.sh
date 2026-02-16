#!/bin/bash
# Automatic cleanup of violations (agent-6x9.5)
# Removes all files matching cleanup patterns

set -e

# Parse arguments
FORCE_MODE=false
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -y|--yes|--force)
            FORCE_MODE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-y|--yes|--force] [--dry-run]"
            echo "  -y, --yes, --force  Skip confirmation prompt (for agents/CI)"
            echo "  -d, --dry-run       Show files that would be deleted without deleting"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check environment variable for agent mode
if [ "${HARNESS_AUTO_CLEANUP:-}" = "true" ] || [ "${HARNESS_AUTO_CLEANUP:-}" = "1" ]; then
    FORCE_MODE=true
fi

echo "🧹 Automatic Cleanup Utility"
echo ""

# Dry-run mode: check if there are violations without exiting
if [ "$DRY_RUN" = true ]; then
    bash .harness/scripts/validate-cleanup.sh || true
    echo ""
    echo "🔍 Dry-run mode: No files were deleted"
    echo ""
    echo "To actually delete these files, run without --dry-run:"
    echo "  bash .harness/scripts/auto-cleanup.sh --yes"
    exit 0
fi

# Dry run first
bash .harness/scripts/validate-cleanup.sh > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Workspace is already clean"
    exit 0
fi

# Show what will be deleted
echo "⚠️  WARNING: This will DELETE files matching cleanup patterns!"
echo ""
echo "Files to be deleted:"
bash .harness/scripts/validate-cleanup.sh 2>&1 | grep "^  -" || true
echo ""

# Dry-run mode: show files without deleting
if [ "$DRY_RUN" = true ]; then
    echo "🔍 Dry-run mode: No files were deleted"
    echo ""
    echo "To actually delete these files, run without --dry-run:"
    echo "  bash .harness/scripts/auto-cleanup.sh --yes"
    exit 0
fi

# Skip confirmation in agent/CI mode
if [ "$FORCE_MODE" = false ] && [ -t 0 ]; then
    read -p "Proceed with cleanup? [y/N]: " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled"
        exit 1
    fi
elif [ "$FORCE_MODE" = true ]; then
    echo "🤖 Agent/CI mode: Proceeding with cleanup (--yes flag detected)"
else
    read -p "Proceed with cleanup? [y/N]: " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleanup cancelled"
        exit 1
    fi
fi

# Load patterns and delete
PATTERNS_FILE=".harness/cleanup_patterns.txt"
DELETED=0

while IFS= read -r pattern; do
    [[ "$pattern" =~ ^#.*$ ]] && continue
    [[ -z "$pattern" ]] && continue
    
    files=$(find . -name "$pattern" \
        ! -path "./.git/*" \
        ! -path "./venv/*" \
        ! -path "./node_modules/*" \
        2>/dev/null || true)
    
    if [ -n "$files" ]; then
        while IFS= read -r file; do
            echo "Removing: $file"
            rm -f "$file"
            DELETED=$((DELETED + 1))
        done <<< "$files"
    fi
done < "$PATTERNS_FILE"

echo ""
echo "✅ Cleanup complete: $DELETED file(s) removed"
