#!/bin/bash
# Automatic cleanup of violations (agent-6x9.5)
# Removes all files matching cleanup patterns

set -e

echo "🧹 Automatic Cleanup Utility"
echo ""
echo "⚠️  WARNING: This will DELETE files matching cleanup patterns!"
echo ""

# Dry run first
bash .harness/scripts/validate-cleanup.sh > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Workspace is already clean"
    exit 0
fi

# Show what will be deleted
echo "Files to be deleted:"
bash .harness/scripts/validate-cleanup.sh 2>&1 | grep "^  -" || true
echo ""

read -p "Proceed with cleanup? [y/N]: " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 1
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
