from datetime import datetime

from agent_harness.agents.sisyphus import sisyphus_orchestrator
from agent_harness.state import ProtocolState


def execution_node(state: ProtocolState) -> ProtocolState:
    """
    Execution node delegating to the Sisyphus team.
    """
    return sisyphus_orchestrator(state)


def human_approval_node(state: ProtocolState) -> ProtocolState:
    """
    Node that explicitly requests human approval.
    LangGraph will interrupt BEFORE this node.
    """
    print(f"✋ Awaiting manual approval for {state['process_id']}")

    # Once continued, we assume approved (or user edited state)
    return {
        **state,
        "awaiting_approval": False,
        "current_phase": "APPROVED",
        "last_updated": datetime.now().isoformat(),
    }
