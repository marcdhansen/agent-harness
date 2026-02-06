import operator
from typing import Annotated, TypedDict


class ProtocolState(TypedDict):
    """
    State definition for the agentic Protocol LangGraph harness.
    Using reducers to allow append-only logic for lists.
    """

    # Process Context
    process_id: str
    process_description: str
    current_phase: str  # Initialization, Execution, Finalization, Retrospective, COMPLETE

    # Task Ledger (Magentic-One pattern)
    goals: Annotated[list[str], operator.add]
    tasks: Annotated[list[dict], operator.add]
    facts_discovered: Annotated[list[str], operator.add]
    educated_guesses: Annotated[list[str], operator.add]

    # Progress Ledger
    steps_completed: Annotated[list[dict], operator.add]
    current_step_index: int
    stall_count: int

    # Compliance State
    initialization_passed: bool
    finalization_passed: bool
    blockers: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]

    # Human-in-Loop
    awaiting_approval: bool
    approval_request: str | None
    user_feedback: str | None

    # Meta
    last_updated: str
