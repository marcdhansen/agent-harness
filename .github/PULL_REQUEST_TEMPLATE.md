# 🚀 Pull Request

## 🔗 Context

- **Issue**: <!-- [Insert Issue ID, e.g., agent-harness-qzo] -->
- **Type**: <!-- [Task | Bug | Feature | Chore] -->

## 📝 Summary of Changes
<!-- Provide a concise summary of the changes made in this PR. -->

## 🧪 Testing & Validation
<!-- Describe the tests run and the results achieved. -->
- [ ] **Unit Tests**: ✅ Passed
- [ ] **Integration Tests**: <!-- ✅ Passed | ❌ N/A -->
- [ ] **Orchestrator Compliance**: ✅ Verified

## ⚠️ Pre-Merge Compliance

> [!IMPORTANT]
> **Required by SOP**: All PRs must use **Rebase and Squash** strategy ([git-workflow.md](../.agent/docs/sop/git-workflow.md))

- [ ] **Branch Rebased**: Rebased onto latest `main` (`git rebase origin/main`)
- [ ] **Commits Squashed**: Single atomic commit (`git log --oneline origin/main..HEAD` shows 1 commit)
- [ ] **No Merge Commits**: Clean linear history (`git log --merges origin/main..HEAD` is empty)
- [ ] **Commit Message Format**: `<type>(<scope>): <description> [<issue-id>]`
- [ ] **Issue ID Present**: Commit message includes Beads issue (e.g., `[agent-harness-xxx]`)
- [ ] **Merge Strategy**: Will use **"Squash and merge"** button (not "Merge pull request")

## 📂 Key Files Modified
<!-- List key files changed/added -->

## 🧠 Session Intelligence

- **Reviewer Note**: <!-- Any specific points the reviewer should focus on or challenges encountered. -->
- **Session Duration**: <!-- Estimated time spent -->

## Standardized Agent Handoff Template
