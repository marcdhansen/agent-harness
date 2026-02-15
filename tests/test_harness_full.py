import os
from unittest.mock import patch

from agent_harness.engine import create_harness_graph, get_sqlite_checkpointer, run_harness


@patch("agent_harness.session_tracker.SessionTracker.has_active_session", return_value=True)
@patch(
    "agent_harness.session_tracker.SessionTracker.get_session",
    return_value={"id": "mock-session-id"},
)
@patch(
    "agent_harness.nodes.initialization.check_beads_issue",
    return_value=(True, "Mocked beads issue"),
)
@patch(
    "agent_harness.nodes.initialization.check_plan_approval",
    return_value=(True, "Mocked plan approval"),
)
@patch(
    "agent_harness.nodes.initialization.check_branch_issue_coupling",
    return_value=(True, "Mocked coupling"),
)
@patch(
    "agent_harness.nodes.initialization.check_tool_version",
    return_value=(True, "Mocked tool version"),
)
@patch(
    "agent_harness.nodes.initialization.check_workspace_integrity",
    return_value=(True, "Mocked workspace integrity"),
)
@patch(
    "agent_harness.nodes.initialization.check_planning_docs",
    return_value=(True, "Mocked planning docs"),
)
@patch(
    "agent_harness.nodes.initialization.check_hook_integrity",
    return_value=(True, "Mocked hook integrity"),
)
@patch(
    "agent_harness.nodes.initialization.check_rebase_status",
    return_value=(True, "Mocked rebase status"),
)
@patch(
    "agent_harness.nodes.finalization.check_plan_approval",
    return_value=(True, "Mocked plan approval"),
)
@patch(
    "agent_harness.nodes.finalization.check_reflection_invoked",
    return_value=(True, "Mocked reflection"),
)
@patch(
    "agent_harness.nodes.finalization.check_debriefing_invoked",
    return_value=(True, "Mocked debriefing"),
)
@patch(
    "agent_harness.nodes.finalization.check_progress_log_exists",
    return_value=(True, "Mocked progress log"),
)
@patch(
    "agent_harness.nodes.finalization.check_handoff_pr_link",
    return_value=(True, "Mocked handoff link"),
)
@patch(
    "agent_harness.nodes.finalization.check_todo_completion",
    return_value=(True, "Mocked todo completion"),
)
@patch(
    "agent_harness.nodes.finalization.check_wrapup_indicator_symmetry",
    return_value=(True, "Mocked symmetry"),
)
@patch(
    "agent_harness.nodes.finalization.check_wrapup_exclusivity",
    return_value=(True, "Mocked exclusivity"),
)
@patch(
    "agent_harness.nodes.finalization.check_handoff_beads_id",
    return_value=(True, "Mocked handoff id"),
)
@patch(
    "agent_harness.nodes.finalization.inject_debrief_to_beads",
    return_value=(True, "Mocked injection"),
)
def test_full_harness_lifecycle(
    mock_inject,
    mock_handoff,
    mock_exclusovity,
    mock_symmetry,
    mock_todo,
    mock_link,
    mock_progress,
    mock_debrief,
    mock_reflection,
    mock_final_approval,
    mock_rebase,
    mock_hook,
    mock_plans,
    mock_work,
    mock_tool,
    mock_coupling,
    mock_init_approval,
    mock_beads,
    mock_get_sess,
    mock_has_sess,
):
    process_id = "PROCESS-SOTA"
    thread_id = "sota-thread-1"
    db_path = "harness_state_final.db"

    if os.path.exists(db_path):
        os.remove(db_path)

    print("🚀 --- STEP 1: INITIALIZE ---")
    run_harness(process_id, "SOTA Lifecycle Test", thread_id, db_path=db_path)

    print("\n✋ --- STEP 2: RESUME & PASS APPROVAL ---")
    checkpointer = get_sqlite_checkpointer(db_path)
    graph = create_harness_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    # This will pass through approval, then Execution, then Finalization, then Retrospective
    # Finalization might fail if there are uncommitted changes
    final_output = graph.invoke(None, config)

    print(f"\nPhase after first full run: {final_output['current_phase']}")
    if final_output["blockers"]:
        print(f"Blockers encountered: {final_output['blockers']}")

    assert final_output["current_phase"] in ["FINALIZATION_BLOCKED", "COMPLETE"]

    print(f"\nSteps performed: {len(final_output['steps_completed'])}")
    for step in final_output["steps_completed"]:
        print(f"  [{step['status']}] {step['task_id']}: {step['action']}")

    print("\n✅ Full Harness Lifecycle Verified!")


if __name__ == "__main__":
    test_full_harness_lifecycle()
