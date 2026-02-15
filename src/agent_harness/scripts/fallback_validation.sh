#!/usr/bin/env bash
# Orchestrator - Fallback Validation Script
# Use this when Python scripts fail or environment is broken.

# CI SKIP HEADER - defense in depth
if [[ "$GITHUB_ACTIONS" == "true" ]] || [[ "$CI" == "true" ]]; then
    echo "ℹ️ Skipping in CI (fallback validation is a local developer tool)"
    exit 0
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}🛡️ ORCHESTRATOR FALLBACK VALIDATION${NC}"
echo -e "========================================"
echo ""

errors=0

echo -e "${BOLD}1. Tool Availability Check${NC}"
for tool in bd git python3 uv gh; do
    if command -v $tool >/dev/null 2>&1; then
        echo -e "  [${GREEN}✅${NC}] $tool: $(which $tool)"
    else
        echo -e "  [${RED}❌${NC}] $tool: NOT FOUND"
        errors=$((errors+1))
    fi
done
echo ""

echo -e "${BOLD}2. Planning Documents Check${NC}"
if [ -f "ImplementationPlan.md" ] || [ -f ".agent/ImplementationPlan.md" ]; then
    echo -e "  [${GREEN}✅${NC}] ImplementationPlan.md: Found"
else
    echo -e "  [${RED}❌${NC}] ImplementationPlan.md: MISSING"
    errors=$((errors+1))
fi

if [ -f "ROADMAP.md" ] || [ -f ".agent/ROADMAP.md" ]; then
    echo -e "  [${GREEN}✅${NC}] ROADMAP.md: Found"
else
    echo -e "  [${YELLOW}⚠️${NC}] ROADMAP.md: MISSING (Optional)"
fi
echo ""

echo -e "${BOLD}3. Git Repository Status${NC}"
if [ -d ".git" ]; then
    BRANCH=$(git branch --show-current)
    echo -e "  [${GREEN}✅${NC}] Git Repo: Detected"
    echo -e "  [${GREEN}✅${NC}] Current Branch: $BRANCH"
    
    CHANGES=$(git status --porcelain | wc -l)
    if [ "$CHANGES" -eq 0 ]; then
        echo -e "  [${GREEN}✅${NC}] Working Tree: Clean"
    else
        echo -e "  [${YELLOW}⚠️${NC}] Working Tree: $CHANGES uncommitted changes"
    fi
else
    echo -e "  [${RED}❌${NC}] Git Repo: NOT DETECTED"
    errors=$((errors+1))
fi
echo ""

echo -e "${BOLD}4. Beads Issue Tracking${NC}"
if [ -f ".beads/current" ]; then
    ISSUE_ID=$(cat .beads/current)
    echo -e "  [${GREEN}✅${NC}] Active Issue: $ISSUE_ID"
else
    echo -e "  [${YELLOW}⚠️${NC}] Active Issue: No issue file detected in .beads/current"
fi
echo ""

echo -e "----------------------------------------"
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ FALLBACK VALIDATION PASSED${NC}"
    echo "Ready to proceed (Manual verification complete)."
    exit 0
else
    echo -e "${RED}${BOLD}❌ FALLBACK VALIDATION FAILED ($errors errors)${NC}"
    echo "Please resolve issues before proceeding."
    exit 1
fi
