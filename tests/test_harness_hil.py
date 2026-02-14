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
    "agent_harness.nodes.finalization.check_plan_approval",
    return_value=(True, "Mocked plan approval"),
)
def test_hil_flow(
    mock_final_approval, mock_coupling, mock_init_approval, mock_beads, mock_get_sess, mock_has_sess
):
    process_id = "HIL-TEST"
    thread_id = "hil-thread-1"
    db_path = "harness_state.db"

    if os.path.exists(db_path):
        os.remove(db_path)

    print("--- FIRST RUN (Should hit interrupt) ---")
    run_harness(process_id, "Testing Human-in-Loop", thread_id)

    # Check if interrupted
    checkpointer = get_sqlite_checkpointer(db_path)
    graph = create_harness_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}}
    state = graph.get_state(config)

    print(f"Current Phase in State: {state.values['current_phase']}")
    print(f"Next Node Expected: {state.next}")

    assert "approval" in state.next
    assert state.values["initialization_passed"] is True

    print("\n--- SECOND RUN (Resuming, should pass interrupt) ---")
    # To pass a node with interrupt_before, we just call invoke(None, config)
    final_result = graph.invoke(None, config)

    # After approval node runs, it continues to Execution and Finalization
    assert final_result["current_phase"] in [
        "APPROVED",
        "Execution",
        "FINALIZATION_BLOCKED",
        "COMPLETE",
    ]
    print("✅ Human-in-Loop and Checkpointing Verified!")


if __name__ == "__main__":
    test_hil_flow()
