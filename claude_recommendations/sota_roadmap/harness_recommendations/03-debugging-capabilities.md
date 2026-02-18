---
title: "Add Comprehensive Debugging Capabilities"
labels: high-priority, developer-experience, enhancement
priority: P1
---

## Problem Statement

No debugging features currently exist, making development and troubleshooting difficult:
- Can't step through agent execution
- No way to inspect state mid-execution
- Can't replay from specific points
- Difficult to understand why agent made certain decisions
- No tool call inspection
- No context window visualization

## Proposed Solution

Implement a comprehensive debugging system:

```python
class HarnessDebugger:
    """Interactive debugging for agent development"""
    
    def __init__(self, harness):
        self.harness = harness
        self.breakpoints = []
        self.step_mode = False
        self.checkpoints = []
        
    def add_breakpoint(self, condition: callable):
        """Break when condition is true"""
        self.breakpoints.append(condition)
        
    def step_through(self):
        """Execute one step at a time"""
        self.step_mode = True
        
    def inspect_state(self) -> dict:
        """Get current agent state"""
        return {
            'messages': self.harness.messages,
            'tools_called': self.harness.tool_history,
            'context_size': self.harness.get_context_tokens(),
            'variables': self.harness.state_vars,
            'permissions': self.harness.permissions.granted_paths
        }
        
    def replay_from_checkpoint(self, checkpoint_id: int):
        """Replay execution from specific checkpoint"""
        checkpoint = self.checkpoints[checkpoint_id]
        self.harness.restore_state(checkpoint)
        
    def trace_tool_call(self, tool_name: str) -> list:
        """Get all inputs/outputs for a specific tool"""
        return [
            call for call in self.harness.tool_history
            if call.tool_name == tool_name
        ]
        
    def visualize_context(self) -> str:
        """Show context window usage"""
        # Visual representation of token usage
        # Highlight what gets trimmed
```

## Key Features

### 1. Interactive Stepping
- Pause before each tool call
- Inspect messages and state
- Modify variables on-the-fly
- Continue or abort execution

### 2. Time-Travel Debugging
- Automatic checkpoint after each step
- Replay from any checkpoint
- Branch from checkpoint with different inputs
- Compare different execution paths

### 3. Tool Call Inspector
- See raw inputs to each tool
- View outputs before agent processes them
- Intercept and modify tool outputs for testing
- Execution time tracking

### 4. Context Window Visualizer
- Real-time token usage display
- Highlight what gets trimmed/compressed
- Preview compression results
- Show prompt caching effectiveness

### 5. Diff Viewer for Code Changes
- Before/after for `edit` tool
- Syntax highlighting
- Ability to reject specific changes
- Git-style diff format

### 6. Conditional Breakpoints
```python
# Break when agent tries to delete files
debugger.add_breakpoint(
    lambda: any('rm' in call.command for call in harness.pending_tools)
)

# Break on specific file access
debugger.add_breakpoint(
    lambda: any('/etc/' in call.path for call in harness.pending_tools)
)
```

## Implementation Details

1. **Create HarnessDebugger class** (`src/agent_harness/debugger.py`)
2. **Add checkpoint system**:
   - Save full state after each step
   - Store in memory (recent 10) and disk (all)
   - Allow restore from any checkpoint
3. **Implement step mode**:
   - Pause before tool execution
   - CLI interface for commands (continue, inspect, abort)
   - Optional web UI for richer experience
4. **Add tool call tracing**:
   - Log all tool inputs/outputs
   - Track execution time
   - Allow filtering by tool name
5. **Create context visualizer**:
   - Calculate token usage
   - Show compression preview
   - Highlight trimmed content
6. **Integrate with harness**:
   - `debug=True` flag in constructor
   - Minimal overhead when disabled
   - CLI commands during execution

## Example Usage

```python
# Start in debug mode
harness = InnerHarness(llm_client=client, debug=True)
debugger = harness.debugger

# Set breakpoint
debugger.add_breakpoint(
    lambda: debugger.context_size > 100000
)

# Step through execution
for step in harness.run_debug("Refactor the codebase"):
    print(f"Step {step.number}: {step.action}")
    state = debugger.inspect_state()
    print(f"Context: {state['context_size']} tokens")
    
    if input("Continue? (y/n/i): ") == 'i':
        # Interactive inspection
        import pdb; pdb.set_trace()
```

## Acceptance Criteria

- [ ] Can enable debug mode with `debug=True`
- [ ] Step-by-step execution works
- [ ] State inspection shows all relevant info
- [ ] Breakpoints trigger correctly
- [ ] Checkpoint/restore works
- [ ] Can replay from any checkpoint
- [ ] Tool call tracing shows inputs/outputs
- [ ] Context visualization displays token usage
- [ ] Diff viewer shows code changes clearly
- [ ] Minimal performance impact when disabled
- [ ] Documentation includes debugging guide
- [ ] Examples show common debugging scenarios

## Dependencies

- Issue #8 (Trajectory Logging) - provides data for replay

## Estimated Effort

Medium (1 week)

## Future Enhancements

- Web-based debugging UI
- Remote debugging support
- Collaborative debugging (share session)
- Debugging recording/playback
- Integration with IDE debuggers
