#!/bin/bash
# shell_scripts/compare-workflows.sh
# Validates old vs new workflow equivalence during parallel run.

set -e

echo "🔍 Comparing CI Workflows Results..."
echo "======================================"

# Check for gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ ERROR: gh CLI not found. Please install it to use this script."
    exit 1
fi

echo "📋 Old Workflow (ci.yml):"
gh run list --workflow=ci.yml --limit=10 --json conclusion,name,createdAt,url | \
    jq -r '.[] | "  - [\(.conclusion)] \(.createdAt) \(.url)"' || echo "  No runs found."

echo ""
echo "📋 New Workflow (pr-ci.yml):"
gh run list --workflow=pr-ci.yml --limit=10 --json conclusion,name,createdAt,url | \
    jq -r '.[] | "  - [\(.conclusion)] \(.createdAt) \(.url)"' || echo "  No runs found."

echo ""
echo "📋 New Workflow (post-merge-ci.yml):"
gh run list --workflow=post-merge-ci.yml --limit=10 --json conclusion,name,createdAt,url | \
    jq -r '.[] | "  - [\(.conclusion)] \(.createdAt) \(.url)"' || echo "  No runs found."

echo ""
echo "✅ Comparison Checklist:"
echo "------------------------"
echo "1. [ ] Same pass/fail outcomes for same commits?"
echo "2. [ ] Similar runtime (±20%)?"
echo "3. [ ] pr-ci.yml warns on linting (yellow) while ci.yml blocked (red)?"
echo "4. [ ] All functional gates (tests) still blocking in pr-ci.yml?"
echo "5. [ ] post-merge-ci.yml correctly creates beads issues on failure?"

echo ""
echo "💡 DECISION MATRIX:"
echo "- ✅ Both pass: Good - equivalent"
echo "- ✅ Both fail: Good - equivalent"
echo "- ⚠️ Old passes, new fails: Investigate - new workflow may be stricter (good)"
echo "- 🚨 Old fails, new passes: CRITICAL - New workflow missing checks!"
# Triggering CI maturation validation
