---
title: "Support Concurrent Agent Execution Without Interference"
labels: high-priority, architecture, enhancement
priority: P1
---

## Problem Statement

Current architecture may have issues with concurrent execution:
- SQLite doesn't handle high concurrency well
- Shared file system could cause conflicts
- Tool state might leak between agents
- No clear isolation strategy
- Risk of race conditions

## Proposed Solution

Implement proper isolation for concurrent agent execution:

```python
class IsolatedAgentSession:
    """Each agent gets completely isolated resources"""
    
    def __init__(self, session_id: str, base_workspace: Path):
        self.session_id = session_id
        
        # Isolated workspace (git worktree)
        self.workspace = self._create_worktree(session_id)
        
        # Isolated database
        self.db_path = f"agent_{session_id}.db"
        
        # Isolated permissions
        self.permission_manager = PermissionManager(self.workspace)
        
        # Isolated sandbox
        self.sandbox = ColimaSandbox(self.workspace)
        
    def _create_worktree(self, session_id: str) -> Path:
        """Create git worktree for this agent"""
        # Uses git worktree for version-controlled isolation
        # Each agent works on separate branch
        return git_worktree_manager.create(session_id)
        
    def __enter__(self):
        """Setup isolated environment"""
        return self
        
    def __exit__(self, *args):
        """Cleanup isolated environment"""
        # Remove worktree
        # Close DB connection
        # Clean temp files
```

## Key Features

### 1. Git Worktree Isolation
Each agent gets own workspace via git worktree:
```python
# Agent 1 workspace
/project/worktree-agent-1/  # Branch: agent/task-1/abc123

# Agent 2 workspace
/project/worktree-agent-2/  # Branch: agent/task-2/def456

# Shared .git directory (read-only for most operations)
/project/.git/
```

**Benefits**:
- Physical file isolation (no collisions)
- Automatic version control
- Built-in merge conflict detection
- Easy rollback per agent
- Audit trail per agent

### 2. Separate Databases
```python
# Instead of shared SQLite:
project.db  # ❌ Lock contention

# Use per-agent DBs:
agent_abc123.db  # ✓ No contention
agent_def456.db  # ✓ No contention
```

### 3. Process-Based vs Thread-Based
```python
# Option 1: Process-based (Recommended)
from multiprocessing import Process

def run_agent(session_id: str, task: str):
    with IsolatedAgentSession(session_id) as session:
        agent = InnerHarness(workspace=session.workspace)
        return agent.run(task)

# Run concurrently
processes = []
for i, task in enumerate(tasks):
    p = Process(target=run_agent, args=(f"agent-{i}", task))
    processes.append(p)
    p.start()

# Wait for completion
for p in processes:
    p.join()

# Option 2: Thread-based (Simpler, but GIL limits)
from concurrent.futures import ThreadPoolExecutor
# ... similar pattern
```

### 4. Resource Limits Per Agent
```python
class ResourceLimits:
    """Enforce limits per agent"""
    max_memory: int = 1024  # MB
    max_cpu_percent: int = 50
    max_execution_time: int = 3600  # seconds
    max_disk_usage: int = 5120  # MB
```

### 5. Safe Merge After Completion
```python
def merge_agent_results(agent_sessions: list[IsolatedAgentSession]):
    """Merge agent work back to main branch"""
    
    for session in agent_sessions:
        result = git_manager.merge_agent_work(
            session.session_id,
            strategy='review'  # Human review if conflicts
        )
        
        if result['status'] == 'conflicts':
            # Handle conflicts
            resolve_conflicts(result['conflicts'])
        else:
            print(f"✓ Agent {session.session_id} merged")
```

## Implementation Details

### 1. Create IsolatedAgentSession class
- Manages all isolation concerns
- Context manager for cleanup
- Resource tracking

### 2. Integrate Git Worktree Manager
- Create worktrees on demand
- Cleanup after merge/completion
- Handle concurrent worktree creation (locking)

### 3. Database Strategy
- Per-agent SQLite files (simple)
- OR shared PostgreSQL with proper transactions (scalable)
- Connection pooling

### 4. Implement Resource Limits
- Use `resource` module (Unix) or `psutil`
- Memory limits via cgroup or ulimit
- CPU throttling via nice/cpulimit
- Disk quotas

### 5. Add Coordinator
```python
class AgentCoordinator:
    """Coordinate multiple concurrent agents"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.active_sessions = {}
        
    def run_agents(self, tasks: list[dict]) -> list:
        """Run multiple agents with coordination"""
        # Enforce max_concurrent limit
        # Handle completion and cleanup
        # Merge results
```

## Concurrent Execution Patterns

### Pattern 1: Independent Tasks
```python
# Multiple unrelated tasks
tasks = [
    "Add error handling to parser.py",
    "Write tests for utils.py",
    "Update README"
]

# Each agent works independently
# No coordination needed
# Merge all at end
```

### Pattern 2: Parallel Decomposition
```python
# Single large task decomposed
task = "Refactor entire codebase"
subtasks = [
    "Refactor src/parser.py",
    "Refactor src/utils.py",
    "Refactor src/main.py"
]

# Agents may conflict - requires coordination
# Merge with conflict resolution
```

### Pattern 3: Pipeline
```python
# Sequential dependencies
pipeline = [
    ("agent-1", "Design API"),
    ("agent-2", "Implement API", deps=["agent-1"]),
    ("agent-3", "Write tests", deps=["agent-2"])
]

# Wait for dependencies before starting
```

## Configuration

```python
concurrent_config = {
    'max_concurrent_agents': 5,
    'isolation_strategy': 'worktree',  # or 'directory'
    'execution_mode': 'process',  # or 'thread'
    'database_strategy': 'per_agent',  # or 'shared'
    'resource_limits': {
        'memory_mb': 1024,
        'cpu_percent': 50,
        'time_seconds': 3600
    },
    'auto_merge': False,  # Require review
    'cleanup_on_complete': True
}
```

## Acceptance Criteria

- [ ] Can run 3-5 agents concurrently without interference
- [ ] Each agent has isolated workspace (worktree)
- [ ] No database lock contention
- [ ] Resource limits enforced per agent
- [ ] Agents can't access each other's files
- [ ] Merge conflicts detected and reported
- [ ] Cleanup happens after completion
- [ ] Process crashes don't affect other agents
- [ ] Performance scales linearly (3 agents != 3x slower)
- [ ] Documentation covers concurrent patterns
- [ ] Tests verify isolation
- [ ] Tests verify merge conflict handling

## Dependencies

- Issue #2 (Sandboxing) - each agent needs sandbox
- Issue #9 (Git Worktree Integration) - worktree management

## Estimated Effort

Medium (1 week)

## Performance Considerations

| Metric | 1 Agent | 3 Agents | 5 Agents |
|--------|---------|----------|----------|
| Disk Usage | 500 MB | 1.5 GB | 2.5 GB |
| Memory | 512 MB | 1.5 GB | 2.5 GB |
| Completion Time | 10 min | 12 min | 15 min |

(Times assume independent tasks; sequential dependencies won't parallelize)

## Future Enhancements

- Agent-to-agent communication
- Shared knowledge base
- Dynamic task allocation
- Auto-scaling (cloud deployment)
- Distributed execution (multiple machines)
