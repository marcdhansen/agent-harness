---
title: "Simplify Inner/Outer Harness Architecture"
labels: medium-priority, architecture, refactor
priority: P2
---

## Problem Statement

The current two-tier architecture (inner vs outer harness) creates confusion:
- Unclear when to use which tier
- Duplicate responsibility between tiers
- Additional cognitive overhead
- May not provide enough value to justify complexity

## Current Architecture

```
┌─────────────────────────────────────────────────────┐
│           OUTER HARNESS (LangGraph)                 │
│  ┌────────┐  ┌──────────┐  ┌──────┐  ┌──────────┐  │
│  │  Init  │─▶│ Approval │─▶│ Exec │─▶│  Final   │  │
│  └────────┘  └──────────┘  └──────┘  └──────────┘  │
│                              │                      │
│                              ▼                      │
│                    ┌─────────────────┐              │
│                    │ INNER HARNESS   │              │
│                    │ (Pi Mono Style) │              │
│                    └─────────────────┘              │
└─────────────────────────────────────────────────────┘
```

**Issues:**
- Why have both?
- When do I use simple vs full mode?
- Can't I just use LangGraph with conditional nodes?

## Proposed Solution

Unify into single harness with execution modes:

```python
class AgentHarness:
    """Unified harness with flexible execution modes"""
    
    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        mode: ExecutionMode = ExecutionMode.SIMPLE,
        **kwargs
    ):
        self.provider = provider
        self.workspace = workspace
        self.mode = mode
        
        # Core components (always present)
        self.tools = self._init_tools()
        self.context = ContextManager()
        self.logger = TrajectoryLogger()
        
        # Optional components (based on mode)
        if mode.needs_approval:
            self.approver = ApprovalGate()
        if mode.needs_orchestration:
            self.graph = self._build_langgraph()
        
    def run(self, task: str, **kwargs):
        """Execute task using configured mode"""
        if self.mode == ExecutionMode.SIMPLE:
            return self._simple_run(task)
        elif self.mode == ExecutionMode.ORCHESTRATED:
            return self._orchestrated_run(task)
        elif self.mode == ExecutionMode.INTERACTIVE:
            return self._interactive_run(task)


class ExecutionMode(Enum):
    """Execution modes with different capabilities"""
    
    SIMPLE = auto()          # Direct execution, no gates
    ORCHESTRATED = auto()    # Full LangGraph workflow
    INTERACTIVE = auto()     # Human-in-loop at each step
    AUTONOMOUS = auto()      # No human intervention
```

## Simplified Architecture

```
┌─────────────────────────────────────────┐
│         UNIFIED AGENT HARNESS           │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Configuration Layer           │   │
│  │  - Execution Mode               │   │
│  │  - Provider Selection           │   │
│  │  - Tool Registry                │   │
│  └─────────────────────────────────┘   │
│                 │                       │
│                 ▼                       │
│  ┌─────────────────────────────────┐   │
│  │   Execution Engine              │   │
│  │  - Simple (Pi Mono style)       │   │
│  │  - Orchestrated (LangGraph)     │   │
│  │  - Interactive (HITL)           │   │
│  └─────────────────────────────────┘   │
│                 │                       │
│                 ▼                       │
│  ┌─────────────────────────────────┐   │
│  │   Core Components               │   │
│  │  - Context Manager              │   │
│  │  - Sandbox                      │   │
│  │  - Trajectory Logger            │   │
│  │  - Debugger                     │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Benefits of Unified Approach

### 1. Single Entry Point
```python
# Before (confusing):
simple_result = InnerHarness(...).run(task)
complex_result = run_harness(...)  # Different API!

# After (unified):
harness = AgentHarness(mode=ExecutionMode.SIMPLE)
simple_result = harness.run(task)

harness = AgentHarness(mode=ExecutionMode.ORCHESTRATED)
complex_result = harness.run(task)
```

### 2. Easier to Understand
- One class to learn
- Mode clearly specified
- Shared components
- Consistent API

### 3. Flexible Mode Switching
```python
# Start simple
harness = AgentHarness(mode=ExecutionMode.SIMPLE)

# Upgrade to orchestrated if needed
harness.switch_mode(ExecutionMode.ORCHESTRATED)

# Or use conditionally
mode = ExecutionMode.ORCHESTRATED if is_critical else ExecutionMode.SIMPLE
harness = AgentHarness(mode=mode)
```

### 4. Better Code Reuse
- Context management shared
- Tools shared
- Logging shared
- Only execution strategy differs

## Implementation Details

### 1. Create Unified AgentHarness Class
- Consolidate InnerHarness and OuterHarness
- Single initialization
- Mode-based behavior

### 2. Define Execution Modes
```python
class ExecutionMode(Enum):
    SIMPLE = {
        'approval_gates': False,
        'langgraph': False,
        'checkpointing': False,
        'human_in_loop': False
    }
    
    ORCHESTRATED = {
        'approval_gates': True,
        'langgraph': True,
        'checkpointing': True,
        'human_in_loop': True
    }
    
    INTERACTIVE = {
        'approval_gates': False,
        'langgraph': False,
        'checkpointing': True,
        'human_in_loop': True  # Every step
    }
```

### 3. Implement Mode-Specific Execution
```python
def _simple_run(self, task: str):
    """Pi Mono style - direct execution"""
    messages = [self._system_prompt(), {'role': 'user', 'content': task}]
    
    while not self._is_complete(messages):
        response = self.provider.complete(messages, tools=self.tools)
        messages.append(response)
        
        if tool_calls := self._extract_tool_calls(response):
            results = self._execute_tools(tool_calls)
            messages.append(results)
    
    return self._extract_result(messages)

def _orchestrated_run(self, task: str):
    """LangGraph workflow with gates"""
    state = self._initialize_state(task)
    
    for step in self.graph.stream(state):
        if step['type'] == 'approval_required':
            if not self._get_approval(step):
                break
        
        self.logger.log_step(step)
    
    return self._extract_result(state)
```

### 4. Migrate Existing Code
- Update examples
- Update tests
- Deprecate old APIs (with warnings)
- Provide migration guide

### 5. Add Mode Selection Helpers
```python
def auto_select_mode(task: str, context: dict) -> ExecutionMode:
    """Intelligently select mode based on task"""
    if context.get('requires_approval'):
        return ExecutionMode.ORCHESTRATED
    elif context.get('is_interactive'):
        return ExecutionMode.INTERACTIVE
    else:
        return ExecutionMode.SIMPLE
```

## Migration Strategy

### Phase 1: Create Unified Class (Week 1)
- Implement AgentHarness
- Preserve existing APIs as wrappers
- All tests still pass

### Phase 2: Update Examples (Week 2)
- Rewrite examples using new API
- Add mode selection guide
- Update documentation

### Phase 3: Deprecation (Week 3+)
- Add deprecation warnings to old APIs
- Provide migration path
- Plan removal for v2.0

## Acceptance Criteria

- [ ] Single AgentHarness class works for all modes
- [ ] Mode switching works
- [ ] All existing tests pass
- [ ] New unified API documented
- [ ] Migration guide provided
- [ ] Examples updated
- [ ] Deprecation warnings in place
- [ ] Performance unchanged

## Dependencies

- Should be done after core features (Issues #1-8)

## Estimated Effort

Medium (1 week)

## Backwards Compatibility

```python
# Old API (deprecated but working):
from agent_harness import InnerHarness, run_harness

inner = InnerHarness(...)  # DeprecationWarning
result = run_harness(...)  # DeprecationWarning

# New API (recommended):
from agent_harness import AgentHarness, ExecutionMode

harness = AgentHarness(mode=ExecutionMode.SIMPLE)
result = harness.run(task)
```

## Future Enhancements

- Custom execution modes (user-defined)
- Mode composition (mix features)
- Runtime mode switching
- Mode presets for common scenarios
