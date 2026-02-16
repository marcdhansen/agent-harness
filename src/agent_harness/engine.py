from __future__ import annotations

from langgraph.graph import END, StateGraph

from agent_harness.nodes.execution import execution_node, human_approval_node
from agent_harness.nodes.finalization import finalization_node, retrospective_node
from agent_harness.nodes.initialization import initialization_node
from agent_harness.persistence import get_sqlite_checkpointer
from agent_harness.state import ProtocolState


def create_harness_graph(checkpointer=None):
    """
    Creates and compiles the agentic Protocol harness graph.
    """
    builder = StateGraph(ProtocolState)

    # Add nodes
    builder.add_node("initialization", initialization_node)
    builder.add_node("approval", human_approval_node)
    builder.add_node("execution", execution_node)
    builder.add_node("finalization", finalization_node)
    builder.add_node("retrospective", retrospective_node)

    # Define workflow
    builder.set_entry_point("initialization")

    # After initialization, if passed, go to approval. If failed, end (blocked).
    def route_after_initialization(state: ProtocolState):
        if state["initialization_passed"]:
            return "approval"
        return END

    builder.add_conditional_edges("initialization", route_after_initialization)

    # After approval (which has an interrupt), go to execution
    builder.add_edge("approval", "execution")

    # After execution, go to finalization
    builder.add_edge("execution", "finalization")

    # After finalization, go to retrospective if passed
    def route_after_finalization(state: ProtocolState):
        if state["finalization_passed"]:
            return "retrospective"
        return END

    builder.add_conditional_edges("finalization", route_after_finalization)
    builder.add_edge("retrospective", END)

    # Compile with checkpointer and interrupt
    return builder.compile(checkpointer=checkpointer, interrupt_before=["approval"])


def run_harness(process_id: str, description: str, thread_id: str, db_path: str | None = None):
    """
    Run the compiled harness graph.
    """
    checkpointer = get_sqlite_checkpointer(db_path)
    graph = create_harness_graph(checkpointer)

    initial_state = {
        "process_id": process_id,
        "process_description": description,
        "current_phase": "INIT",
        "goals": [],
        "tasks": [],
        "facts_discovered": [],
        "educated_guesses": [],
        "steps_completed": [],
        "current_step_index": 0,
        "stall_count": 0,
        "initialization_passed": False,
        "finalization_passed": False,
        "blockers": [],
        "warnings": [],
        "awaiting_approval": True,
        "approval_request": f"Approve start of process {process_id}",
        "user_feedback": None,
        "last_updated": "",
    }

    config = {"configurable": {"thread_id": thread_id}}

    # Check if we have existing state (resume)
    state = graph.get_state(config)
    if state and state.values:
        print(f"🔄 Resuming process {process_id} from {state.values['current_phase']}")
        return graph.invoke(None, config)
    else:
        print(f"🚀 Starting process {process_id}")
        return graph.invoke(initial_state, config)
