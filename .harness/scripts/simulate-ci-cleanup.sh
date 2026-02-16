#!/bin/bash
# Simulate CI cleanup validation locally (agent-6x9.2)
# Helps catch issues before pushing to CI


set -e


echo "🔍 Simulating CI cleanup validation..."
echo ""


BASE_BRANCH="${1:-main}"
echo "Base branch: $BASE_BRANCH"
echo ""


echo "Files changed in current branch:"
CHANGED_FILES=$(git diff --name-only --diff-filter=AM origin/$BASE_BRANCH...HEAD 2>/dev/null || git diff --name-only --diff-filter=AM $BASE_BRANCH...HEAD 2>/dev/null || echo "")


if [ -z "$CHANGED_FILES" ]; then
  echo "  (no files changed)"
  echo ""
  echo "✅ No files to validate"
  exit 0
fi


echo "$CHANGED_FILES" | sed 's/^/  - /'
echo ""


if [ ! -f .harness/cleanup_patterns.txt ]; then
  echo "⚠️  Pattern file not found: .harness/cleanup_patterns.txt"
  echo "Skipping validation"
  exit 0
fi


echo "Checking against cleanup patterns..."
VIOLATIONS=()


while IFS= read -r pattern; do
  [[ "$pattern" =~ ^#.*$ ]] && continue
  [[ -z "$pattern" ]] && continue

  regex_pattern=$(echo "$pattern" | sed 's/\./\\./g' | sed 's/\*/.*/g' | sed 's/\?/./g')

  while IFS= read -r file; do
    if echo "$file" | grep -qE "^${regex_pattern}$"; then
      VIOLATIONS+=("$file")
    fi
  done <<< "$CHANGED_FILES"
done < .harness/cleanup_patterns.txt


VIOLATIONS=($(printf '%s\n' "${VIOLATIONS[@]}" | sort -u))


echo ""
if [ ${#VIOLATIONS[@]} -gt 0 ]; then
  echo "❌ VALIDATION WOULD FAIL IN CI"
  echo ""
  echo "Temporary files detected:"
  printf '  - %s\n' "${VIOLATIONS[@]}"
  echo ""
  echo "Fix before pushing:"
  printf '  git rm %s\n' "${VIOLATIONS[@]}"
  echo ""
  exit 1
else
  echo "✅ No violations detected"
  echo "CI cleanup validation will pass"
  echo ""
  exit 0
fi
