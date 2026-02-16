#!/bin/bash
# Git hooks installer (agent-6x9.1)
# Installs agent harness git hooks


set -e


echo "🔧 Installing agent harness git hooks..."
echo ""


# Hook types to install (expand as new hooks are added)
HOOKS=(
    "pre-commit"
    # "pre-push"     # TODO: Add in agent-6x9.2 (CI/CD validation)
    # "commit-msg"   # TODO: Add in future phases if needed
)


# Counters
INSTALLED=0
SKIPPED=0
BACKED_UP=0


# Install each hook type
for hook in "${HOOKS[@]}"; do
    SOURCE_HOOK=".harness/hooks/$hook"
    TARGET_HOOK=".git/hooks/$hook"

    # Check if source hook exists
    if [ ! -f "$SOURCE_HOOK" ]; then
        echo "⏭️  Skipping $hook (not yet implemented)"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Backup existing hook if present
    if [ -f "$TARGET_HOOK" ]; then
        TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        BACKUP="${TARGET_HOOK}.backup.${TIMESTAMP}"
        echo "📦 Backing up existing $hook hook"
        echo "   → $BACKUP"
        cp "$TARGET_HOOK" "$BACKUP"
        BACKED_UP=$((BACKED_UP + 1))
    fi

    # Install hook
    echo "📋 Installing $hook hook..."
    cp "$SOURCE_HOOK" "$TARGET_HOOK"
    chmod +x "$TARGET_HOOK"
    INSTALLED=$((INSTALLED + 1))
    echo "✅ $hook hook installed"
    echo ""
done


# Show installed hooks
if [ $INSTALLED -gt 0 ]; then
    echo ""
    echo "📄 Installed hooks:"
    for hook in "${HOOKS[@]}"; do
        TARGET_HOOK=".git/hooks/$hook"
        if [ -x "$TARGET_HOOK" ]; then
            ls -lh "$TARGET_HOOK"
        fi
    done
fi


# Show hook components
if [ -d .harness/hooks/pre-commit.d ]; then
    echo ""
    echo "🔧 Pre-commit components:"
    ls -lh .harness/hooks/pre-commit.d/
fi


# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Hook installation complete"
echo ""
echo "Summary:"
echo "  • Installed: $INSTALLED hook(s)"
[ $BACKED_UP -gt 0 ] && echo "  • Backed up: $BACKED_UP existing hook(s)"
[ $SKIPPED -gt 0 ] && echo "  • Skipped: $SKIPPED hook(s) (not yet implemented)"
echo ""
echo "To update hooks in the future, run:"
echo "  bash .harness/install_hooks.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
