# Hotfix Development Rules for Agent Harness

## Overview

This document defines hotfix development protocols for agent harness systems using trunk-based development with release branches. The goal is to balance emergency response speed with long-term code stability and maintainability.

---

## I. Architectural Requirements

These are system-level requirements that must be in place before hotfix workflows can function properly.

### A. Branching Strategy

**Model:** Trunk-Based Development with Release Branches
- **Trunk branch:** `main` (or `master`)
- **Release branches:** `release/v1.x`, `release/v2.x`, etc.
- **Development branches:** Feature branches that merge to trunk
- **Hotfix branches:** Short-lived branches for emergency fixes

**Note:** This is NOT pure trunk-based development - it's a hybrid model that uses trunk for feature work but maintains release branches for production versions.

### B. CI/CD Pipeline Requirements

The following automation must be configured:

1. **Version Auto-Increment**
   - Hotfix merges automatically bump patch version (e.g., `v1.2.3` → `v1.2.4`)
   - Uses semantic versioning (MAJOR.MINOR.PATCH)

2. **Beads Ticket Integration**
   - Auto-update ticket status when hotfix branch is created
   - Auto-close ticket when hotfix is deployed
   - Link commits to ticket IDs in commit messages

3. **Automated Back-Merge**
   - After hotfix to release branch, auto-create PR to merge back to trunk
   - Prevents code divergence between production and development

4. **Deployment Safety**
   - Automated rollback triggers on deployment failure
   - Canary deployment for gradual rollout (configurable)
   - Health check gates before full deployment

### C. Break-Glass Protocols

For critical production outages:

1. **Emergency Override Permissions**
   - Senior engineers can bypass branch protection
   - Requires incident ticket number
   - All bypasses logged to audit system

2. **Traceability Requirements**
   - Override actions must include incident ID
   - Automated post-incident review ticket creation
   - Slack/email notifications to team

---

## II. Process Requirements

These are the steps agents must follow when handling hotfixes.

### A. Testing Gates

**Before any deployment:**
1. All existing automated tests must pass
2. Hotfix-specific tests must be added
3. Manual smoke test checklist completed (if applicable)

**Exception:** In critical P0 outages, testing may be expedited but not skipped. Document testing decisions in ticket.

### B. Communication Protocol

**Required notifications:**
1. **On hotfix start:** Post to team channel with ticket link
2. **Before deployment:** Alert stakeholders with deployment plan
3. **After deployment:** Status update with verification results
4. **Post-incident:** Share post-mortem findings

### C. Documentation Requirements

Each hotfix must include:
1. **Root cause analysis** in the Beads ticket
2. **Fix description** explaining the change
3. **Testing notes** documenting verification
4. **Rollback procedure** (if complex)

---

## III. Decision Tree: Choosing Hotfix Approach

Use this decision tree to determine the correct hotfix workflow:

```
START: Production issue detected
│
├─ Q1: Is production currently down or degraded?
│  │
│  ├─ YES → Use EMERGENCY HOTFIX (Section IV-A)
│  │
│  └─ NO → Continue to Q2
│
├─ Q2: Does trunk contain unreleased features?
│  │
│  ├─ YES → Use RELEASE-FIRST HOTFIX (Section IV-B)
│  │
│  └─ NO → Continue to Q3
│
└─ Q3: Can this wait for next release?
   │
   ├─ YES → Create regular issue, not a hotfix
   │
   └─ NO → Use TRUNK-FIRST HOTFIX (Section IV-C)
```

### Decision Criteria Details

**Q1: Production Down/Degraded**
- **Down:** Users cannot access system
- **Degraded:** Significantly impaired functionality (>50% failure rate, security breach, data loss)
- **Action:** Emergency hotfix bypasses standard approval

**Q2: Trunk Has Unreleased Features**
- **Check:** Compare trunk to latest release tag
- **If uncertain:** Use release-first approach (safer)
- **Why it matters:** Hotfixing trunk could leak unreleased code to production

**Q3: Can Wait for Next Release**
- **Consider:** Severity, customer impact, business risk
- **When to wait:** Minor bugs, cosmetic issues, workarounds exist
- **When NOT to wait:** Security vulnerabilities, data integrity issues, major customer pain

---

## IV. Step-by-Step Hotfix Procedures

### A. Emergency Hotfix (P0 Outage)

**When to use:** Production is down or critically degraded right now.

**Steps:**

1. **Create incident ticket**
   ```bash
   bd create "P0: Production outage - [brief description]" \
     --priority 0 \
     --type bug \
   --labels emergency,production
   ```

2. **Branch from affected release**
   ```bash
   git checkout release/v2.1
   git pull origin release/v2.1
   git checkout -b hotfix/TICKET_ID-brief-description
   ```

3. **Implement minimal fix**
   - Focus ONLY on restoring service
   - Do NOT include refactoring or improvements
   - Add targeted test if time permits

4. **Commit with ticket reference**
   ```bash
   git commit -m "hotfix(TICKET_ID): [description]
   
   Resolves TICKET_ID
   
   Emergency fix for production outage.
   Root cause: [brief explanation]
   "
   ```

5. **Deploy using break-glass if needed**
   ```bash
   # If branch protection blocks:
   # 1. Use emergency override with incident ID
   # 2. Push directly to release branch
   # 3. Document in ticket
   
   git push origin hotfix/TICKET_ID-brief-description
   # Create PR or use emergency merge
   ```

6. **Verify deployment**
   - Check health endpoints
   - Monitor error rates
   - Confirm customer impact resolved

7. **Forward-port to trunk**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b backmerge/TICKET_ID
   git merge hotfix/TICKET_ID-brief-description
   # Resolve conflicts if any
   git push origin backmerge/TICKET_ID
   # Create PR to main
   ```

8. **Update Beads ticket**
   ```bash
   bd update TICKET_ID --status closed
   bd create "Post-incident review for TICKET_ID" \
     --type task \
     --priority 1 \
     --labels postmortem \
     --blocks-by TICKET_ID
   ```

**Automation support:**
- CI/CD auto-increments patch version on merge
- Beads auto-updates ticket status
- Monitoring triggers rollback if deployment fails

---

### B. Release-First Hotfix (Trunk Has Unreleased Code)

**When to use:** Trunk contains unreleased features that shouldn't go to production yet.

**Steps:**

1. **Create hotfix ticket**
   ```bash
   bd create "Hotfix: [description]" \
     --priority 1 \
     --type bug \
     --labels hotfix,production
   ```

2. **Branch from release branch**
   ```bash
   git checkout release/v2.1
   git pull origin release/v2.1
   git checkout -b hotfix/TICKET_ID-description
   ```

3. **Implement and test fix**
   - Write fix
   - Add regression test
   - Run full test suite
   ```bash
   # Run tests
   npm test  # or your test command
   ```

4. **Create PR to release branch**
   ```bash
   git push origin hotfix/TICKET_ID-description
   # Create PR to release/v2.1
   # Get required approvals
   ```

5. **Merge to release and deploy**
   - Merge PR to release branch
   - CI/CD auto-deploys to production
   - Monitor deployment

6. **Forward-port to trunk**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b backmerge/TICKET_ID
   git cherry-pick <hotfix-commit-sha>
   # Or: git merge hotfix/TICKET_ID-description
   git push origin backmerge/TICKET_ID
   # Create PR to main
   ```

7. **Close ticket**
   ```bash
   bd close TICKET_ID --reason "Fixed in v2.1.4, forward-ported to main"
   ```

**Key point:** Release branch is fixed first, THEN changes are brought forward to trunk via cherry-pick or merge.

---

### C. Trunk-First Hotfix (Clean Trunk)

**When to use:** Trunk is clean (no unreleased features) and issue is not P0.

**Steps:**

1. **Create hotfix ticket**
   ```bash
   bd create "Hotfix: [description]" \
     --priority 1 \
     --type bug \
     --labels hotfix
   ```

2. **Branch from trunk**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/TICKET_ID-description
   ```

3. **Implement fix with tests**
   - Write fix
   - Add regression test
   - Ensure all tests pass

4. **Create PR to trunk**
   ```bash
   git push origin hotfix/TICKET_ID-description
   # Create PR to main
   # Get approvals
   ```

5. **Merge to trunk**
   - Merge PR
   - CI/CD auto-increments version

6. **Cherry-pick to release branch**
   ```bash
   git checkout release/v2.1
   git pull origin release/v2.1
   git cherry-pick <hotfix-commit-sha>
   git push origin release/v2.1
   ```

7. **Deploy from release branch**
   - CI/CD auto-deploys patched release
   - Monitor deployment

8. **Close ticket**
   ```bash
   bd close TICKET_ID --reason "Fixed in main and backported to v2.1"
   ```

**Key point:** Trunk is fixed first, THEN changes are backported to release branches.

---

## V. Handling Edge Cases

### A. Multiple Release Branches Affected

If bug exists in multiple release versions (e.g., v2.1 and v3.0):

1. Fix oldest affected version first
2. Cherry-pick fix to newer versions
3. Forward-port to trunk last

**Example:**
```bash
# Fix in v2.1
git checkout release/v2.1
git checkout -b hotfix/TICKET_ID
# ... implement fix ...
git push origin hotfix/TICKET_ID

# Cherry-pick to v3.0
git checkout release/v3.0
git cherry-pick <hotfix-commit>
git push origin release/v3.0

# Forward-port to main
git checkout main
git cherry-pick <hotfix-commit>
git push origin main
```

### B. Hotfix Introduces Regression

If deployed hotfix causes new issues:

1. **Immediately rollback**
   ```bash
   # CI/CD should auto-rollback on health check failure
   # Or manual: revert deployment to previous version
   ```

2. **Create new P0 ticket**
   ```bash
   bd create "P0: Hotfix regression - [description]" \
     --priority 0 \
     --type bug \
     --labels emergency,regression \
     --blocks-by ORIGINAL_TICKET_ID
   ```

3. **Fix the fix**
   - Follow emergency hotfix procedure
   - Include additional tests to prevent recurrence

### C. Merge Conflicts During Forward-Port

When cherry-picking to trunk creates conflicts:

1. **Resolve conflicts manually**
   ```bash
   git checkout main
   git cherry-pick <hotfix-commit>
   # Conflicts appear
   # Resolve in editor
   git add .
   git cherry-pick --continue
   ```

2. **Re-run full test suite**
   - Conflicts may break unrelated code
   - Verify everything still works

3. **Create PR for review**
   - Even if you're senior, get second pair of eyes
   - Conflict resolution can introduce subtle bugs

---

## VI. Validation Checklist

Before marking hotfix complete, verify:

- [ ] Fix is deployed to production
- [ ] Health checks passing
- [ ] Error rates returned to normal
- [ ] Customer impact confirmed resolved
- [ ] Beads ticket updated with closure notes
- [ ] Fix forward-ported to trunk (or documented why not)
- [ ] Post-incident review scheduled (for P0s)
- [ ] Team notified of completion

---

## VII. Anti-Patterns to Avoid

**DON'T:**
1. ❌ Hotfix trunk when it has unreleased features (use release-first)
2. ❌ Skip tests because "it's urgent" (add minimal test at least)
3. ❌ Forget to forward-port to trunk (creates divergence)
4. ❌ Batch multiple fixes in one hotfix (increases risk)
5. ❌ Deploy without rollback plan
6. ❌ Skip ticket updates (loses traceability)

**DO:**
1. ✅ Keep hotfix scope minimal
2. ✅ Add regression tests
3. ✅ Forward-port promptly (same day)
4. ✅ Document root cause
5. ✅ Use automation for version bumps and merges
6. ✅ Monitor deployment closely

---

## VIII. Metrics to Track

Monitor these to improve hotfix process:

1. **Time to Deploy** - From incident detection to fix in production
2. **Forward-Port Lag** - Time between release fix and trunk merge
3. **Hotfix Rework Rate** - % of hotfixes that need a second attempt
4. **Test Coverage Impact** - Tests added per hotfix
5. **Automation Success Rate** - % of auto-merges that succeed

**Target SLAs:**
- P0 hotfixes: <2 hours to deployment
- P1 hotfixes: <24 hours to deployment
- Forward-port lag: <1 business day
- Test coverage: 100% of hotfixes include tests

---

## IX. Tool Configuration Notes

### Beads Integration

**Required Beads fields for hotfixes:**
- `priority`: 0 (emergency) or 1 (urgent)
- `type`: bug
- `labels`: Must include `hotfix` and optionally `emergency`, `production`

**Automation hooks:**
- Hotfix branch creation → Auto-update ticket to `in_progress`
- PR merge → Auto-update ticket to `deployed`
- Deployment success → Auto-close ticket

**Dependency tracking:**
- Link hotfix to original bug report: `--blocks-by BUG_TICKET_ID`
- Link post-incident review: `--discovered-from HOTFIX_TICKET_ID`

### CI/CD Configuration

**Required pipeline stages:**
1. Automated tests (blocking)
2. Version bump (auto-increment PATCH)
3. Build and package
4. Deploy to staging
5. Health checks (blocking)
6. Deploy to production (canary or blue-green)
7. Production health checks
8. Rollback trigger on failure
9. Back-merge PR creation

---

## X. Summary of Key Principles

1. **Speed with Safety** - Automation handles the fast path, tests ensure quality
2. **Upstream-First When Possible** - But release-first when trunk is ahead
3. **Always Forward-Port** - No divergence between release and trunk
4. **Track Everything** - Beads tickets and git history provide full audit trail
5. **Automate, Don't Trust Memory** - Humans forget under pressure, CI/CD doesn't
6. **Rollback Over Debug** - If in doubt, revert and investigate offline

---

## Appendix: Quick Reference

### Emergency Hotfix (P0)
```
1. Create ticket (priority 0)
2. Branch from release/vX.Y
3. Fix + minimal test
4. Deploy (use break-glass if needed)
5. Forward-port to main
6. Update ticket
```

### Release-First Hotfix
```
1. Create ticket (priority 1)
2. Branch from release/vX.Y
3. Fix + full tests
4. PR → release branch
5. Deploy
6. Cherry-pick → main
7. Close ticket
```

### Trunk-First Hotfix
```
1. Create ticket (priority 1)
2. Branch from main
3. Fix + full tests
4. PR → main
5. Cherry-pick → release branch
6. Deploy from release
7. Close ticket
```
