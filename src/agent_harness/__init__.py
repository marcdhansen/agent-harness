"""Agentic Protocol Harness - Standard Protocol for AI Agent Orchestration."""

from agent_harness.engine import create_harness_graph, run_harness
from agent_harness.inner import InnerHarness
from agent_harness.session_tracker import (
    CleanupViolationError,
    SessionTracker,
    ValidationResult,
)
from agent_harness.state import ProtocolState

# Worktree management (agent-6x9.4)
_worktree_available = True
try:
    from agent_harness.git_worktree_manager import (
        GitWorktreeManager,  # noqa: F401
        WorktreeCleanupError,  # noqa: F401
    )
except ImportError:
    _worktree_available = False

__all__ = [
    "InnerHarness",
    "ProtocolState",
    "create_harness_graph",
    "run_harness",
    "SessionTracker",
    "CleanupViolationError",
    "ValidationResult",
]

if _worktree_available:
    __all__.extend(
        [
            "GitWorktreeManager",
            "WorktreeCleanupError",
        ]
    )

__version__ = "0.1.0"
# test
