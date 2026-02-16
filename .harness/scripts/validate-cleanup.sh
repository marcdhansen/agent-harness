#!/bin/bash
# Quick cleanup validation (agent-6x9.5)
# Validates workspace without full compliance check

set -e

echo "🔍 Quick Cleanup Validation"
echo ""

# Load patterns
PATTERNS_FILE=".harness/cleanup_patterns.txt"

if [ ! -f "$PATTERNS_FILE" ]; then
    echo "❌ Patterns file not found: $PATTERNS_FILE"
    exit 1
fi

# Scan for violations
echo "Scanning workspace..."
VIOLATIONS=()

while IFS= read -r pattern; do
    # Skip comments and empty lines
    [[ "$pattern" =~ ^#.*$ ]] && continue
    [[ -z "$pattern" ]] && continue
    
    # Find matching files
    files=$(find . -name "$pattern" \
        ! -path "./.git/*" \
        ! -path "./venv/*" \
        ! -path "./node_modules/*" \
        2>/dev/null || true)
    
    if [ -n "$files" ]; then
        while IFS= read -r file; do
            VIOLATIONS+=("$file")
        done <<< "$files"
    fi
done < "$PATTERNS_FILE"

# Report
echo ""
if [ ${#VIOLATIONS[@]} -eq 0 ]; then
    echo "✅ No cleanup violations found"
    echo "Workspace is clean!"
    exit 0
else
    echo "⚠️  Found ${#VIOLATIONS[@]} violation(s):"
    for v in "${VIOLATIONS[@]}"; do
        echo "  - $v"
    done
    echo ""
    echo "To clean up:"
    echo "  rm <file>  # Remove individual files"
    echo "  bash .harness/scripts/auto-cleanup.sh  # Auto-remove all"
    exit 1
fi
