# 📋 Standard Operating Procedure (SOP) Compliance Checklist (Generated)

> **Source of Truth**: The JSON files in `.agent/rules/checklists/` define the authoritative workflow.

## ⚡ Phases

### Phase 2: Initialization — MANDATORY

Verify environment, tools, and planning readiness.

- [ ] **Verify 'bd' tool version** (Validator: `check_tool_version`)
- [ ] **Verify 'git' tool version** (Validator: `check_tool_version`)
- [ ] **Verify mandatory directories (.git, .agent, .beads)** (Validator: `check_workspace_integrity`)
- [ ] **Verify planning documents exist (ROADMAP.md, ImplementationPlan.md)** (Validator: `check_planning_docs`)
- [ ] **Verify active Beads issue exists** (Validator: `check_beads_issue`)
- [ ] **Verify plan approval is fresh (<4h)** (Validator: `check_plan_approval`)

### Phase 3: Planning — MANDATORY

Define proposed changes, blast radius, and success criteria.

- [ ] **Update ImplementationPlan.md with proposed changes** (Validator: `check_planning_docs`)
- [ ] **Perform blast radius analysis** (Validator: `check_planning_docs`)
- [ ] **Get explicit user approval before EXECUTION** (Validator: `check_plan_approval`)
- [ ] **Include API design documentation if feature involves API changes** (Validator: `check_api_documentation`)
- [ ] **Create beads issue(s) after approval (BLOCKER before execution)** - Use `bd create` with plan reference in description
- [ ] **Store plan in .agent/plans/{issue-id}.md with bi-directional links** (Validator: `check_plan_storage`)

### Phase 4: Execution — MANDATORY

Active work phase - executing the task.

- [ ] **Verify on a feature branch** (Validator: `check_branch_info`)
- [ ] **Verify task.md exists in brain directory** (Validator: `check_workspace_integrity`)
- [ ] **Verify active Beads issue exists** (Validator: `check_beads_issue`)
- [ ] **Verify plan approval (MANDATORY for Execution)** (Validator: `check_plan_approval`)
- [ ] **Verify beads issue created after plan approval** (BLOCKER: Must create issue(s) after approval before execution)
- [ ] **Verify plan stored in .agent/plans/{issue-id}.md** (Validator: `check_plan_storage`)
- [ ] **Verify TDD compliance** (Validator: `validate_tdd_compliance`)

### Phase 5: Finalization — MANDATORY

Quality gates, atomic commits, TDD validation, and PR creation.

- [ ] **Verify working tree is clean** (Validator: `check_git_status`)
- [ ] **Validate atomic commit requirements and conventional format** (Validator: `validate_atomic_commits`)
- [ ] **Validate TDD compliance (implementation accompanied by tests)** (Validator: `validate_tdd_compliance`)
- [ ] **Verify structured reflection was captured (.reflection_input.json)** (Validator: `check_reflection_invoked`)
- [ ] **Verify hand-off documentation exists (.agent/handoffs/{issue-id}.md)** (Validator: `check_handoff_completed`)
- [ ] **Verify handoff file will be cleaned up on issue close** - Handoff files in `.agent/handoffs/` are automatically deleted when the associated beads issue is closed after PR merge
- [ ] **Verify no orphaned or multiple open PRs for the task** (Validator: `check_handoff_pr_verification`)
- [ ] **Verify PR references the active Beads issue** (Validator: `check_beads_pr_sync`)
- [ ] **Verify the workspace is clean of temporary artifacts** (Validator: `check_workspace_cleanup`)

### Phase 6: Retrospective — MANDATORY

Strategic learning, session closure, and handoff.

- [ ] **Verify structured reflection was captured (.reflection_input.json)** (Validator: `check_reflection_invoked`)
- [ ] **Verify mission debriefing file exists** (Validator: `check_debriefing_invoked`)
- [ ] **Verify plan approval marker is cleared in task.md** (Validator: `check_plan_approval`)
- [ ] **Verify reflector synthesis in progress log** (Validator: `check_progress_log_exists`)
- [ ] **Verify GitHub PR link in debrief.md** (Validator: `check_handoff_pr_link`)
- [ ] **Verify Beads issue ID in debrief.md** (Validator: `check_handoff_beads_id`)
- [ ] **Verify all tasks in task.md are completed** (Validator: `check_todo_completion`)

### Phase 7: Clean State Validation — MANDATORY

Final verification: repo should be clean after PR merge.

- [ ] **Verify on main/master branch** (Validator: `check_branch_info`)
- [ ] **Verify working tree is clean** (Validator: `check_git_status`)
- [ ] **Verify up to date with remote** (Validator: `check_git_status`)
- [ ] **Verify temporary artifacts removed (task.md, debrief.md, etc.)** (Validator: `check_workspace_integrity`)

---

## Reference Documents

- [.agent/rules/coding-principles.md](./rules/coding-principles.md) - Core coding principles (Prevent/Detect/Correct, Fail Loudly, Treat Cause Not Symptom)
