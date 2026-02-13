---
title: "Integrate Git Worktrees for Agent Workspace Isolation"
labels: high-priority, architecture, enhancement
priority: P1
---

## Problem Statement

Need robust isolation for concurrent agents that also provides:
- Automatic version control of agent actions
- Merge conflict detection
- Easy rollback of agent work
- Audit trail per agent

Git worktrees provide all of this while being lightweight.

## Proposed Solution

Use git worktrees to give each agent an isolated, version-controlled workspace:

```python
class GitWorktreeManager:
    """Manage git worktrees for agent isolation"""
    
    def __init__(self, repo_path: Path):
        self.repo = Repo(repo_path)
        self._lock = threading.Lock()
        self._active_worktrees = {}
        
    def create_worktree(self, agent_id: str, base_branch: str = "main") -> Path:
        """Create isolated worktree for agent"""
        with self._lock:  # Serialize git operations
            branch = f"agent/{agent_id}/{uuid4().hex[:8]}"
            worktree_path = self.repo.working_dir.parent / f"agent-{agent_id}"
            
            # Create worktree from base branch
            self.repo.git.worktree('add', str(worktree_path), '-b', branch, base_branch)
            
            self._active_worktrees[agent_id] = {
                'path': worktree_path,
                'branch': branch,
                'created': datetime.now()
            }
            
            return worktree_path
    
    def remove_worktree(self, agent_id: str, keep_branch: bool = False):
        """Remove worktree and optionally branch"""
        workspace = self._active_worktrees.get(agent_id)
        if not workspace:
            return
            
        with self._lock:
            # Remove worktree
            self.repo.git.worktree('remove', str(workspace['path']), '--force')
            
            # Optionally delete branch
            if not keep_branch:
                self.repo.git.branch('-D', workspace['branch'])
                
            del self._active_worktrees[agent_id]
    
    def merge_agent_work(self, agent_id: str, target: str = "main") -> dict:
        """Merge agent's branch back to target"""
        workspace = self._active_worktrees.get(agent_id)
        if not workspace:
            raise ValueError(f"No worktree for {agent_id}")
        
        with self._lock:
            try:
                # Checkout target
                self.repo.git.checkout(target)
                
                # Attempt merge
                self.repo.git.merge(
                    workspace['branch'],
                    '--no-ff',
                    '-m', f"Merge agent work: {agent_id}"
                )
                
                return {'status': 'merged', 'conflicts': []}
                
            except GitCommandError as e:
                if 'CONFLICT' in str(e):
                    conflicts = self._parse_conflicts()
                    return {
                        'status': 'conflicts',
                        'conflicts': conflicts,
                        'message': 'Manual resolution required'
                    }
                raise
```

## Key Benefits

### 1. Automatic Version Control
Every agent action is tracked in git:
```bash
# See what agent did
git log agent/task-123/abc456

# See specific changes
git diff main..agent/task-123/abc456
```

### 2. Built-in Merge Conflict Detection
When multiple agents touch same files:
```python
# Agent 1 and 2 both modified parser.py
merge_result = manager.merge_agent_work("agent-1")
# Returns: {'status': 'conflicts', 'files': ['parser.py']}

# Human can review and resolve
```

### 3. Easy Rollback
```bash
# Agent made bad changes? Just delete the branch
git worktree remove agent-1-workspace
git branch -D agent/task-123/abc456

# Try different approach
# Create new worktree from same starting point
```

### 4. Audit Trail
```python
# Each agent commits with descriptive messages
workspace.commit("""
Refactored parser for better error handling

Changes:
- Added try/except blocks
- Improved error messages
- Added logging

Reasoning: {agent_reasoning}
""")

# Later: review exactly what agent did and why
```

## Implementation Details

### 1. Create GitWorktreeManager Class
(`src/agent_harness/git_worktree.py`)

### 2. Integrate with AgentWorkspace
```python
class AgentWorkspace:
    """Represents agent's isolated workspace"""
    
    def __init__(self, path: Path, branch: str, agent_id: str):
        self.path = path
        self.branch = branch
        self.agent_id = agent_id
        self._repo = Repo(path)
    
    def commit(self, message: str):
        """Commit current changes"""
        self._repo.git.add('-A')
        self._repo.git.commit('-m', f'[{self.agent_id}] {message}')
    
    def get_diff(self, target: str = "main") -> str:
        """Get diff against target branch"""
        return self._repo.git.diff(f'{target}..{self.branch}')
```

### 3. Handle Git Operations Safely
- **Lock all git operations** (shared .git directory)
- **Retry on lock failures**
- **Validate repository state** before operations

### 4. Storage Optimization
For large repos, worktrees duplicate working files:
```python
# Sparse checkout for large repos
def create_sparse_worktree(self, agent_id: str, paths: list[str]):
    """Create worktree with only specified paths"""
    worktree = self.create_worktree(agent_id)
    
    # Configure sparse checkout
    sparse_checkout_file = worktree / '.git/info/sparse-checkout'
    sparse_checkout_file.write_text('\n'.join(paths))
    
    subprocess.run(['git', 'sparse-checkout', 'reapply'], cwd=worktree)
```

### 5. Cleanup Strategy
```python
class WorktreeCleanupPolicy:
    """Policy for worktree cleanup"""
    
    # When to cleanup
    on_merge: bool = True        # After successful merge
    on_error: bool = False       # Keep for debugging
    on_session_end: bool = True  # End of agent session
    
    # What to keep
    keep_branch: bool = False    # Delete branch after cleanup
    keep_commits: bool = True    # Merge to archive branch
```

## Git Worktree Patterns

### Pattern 1: Simple Task
```python
with git_manager.agent_workspace("agent-1") as workspace:
    # Agent works in workspace.path
    agent = InnerHarness(workspace=workspace.path)
    result = agent.run("Add error handling")
    
    # Commit work
    workspace.commit("Added error handling to parser")

# Merge back
merge_result = git_manager.merge_agent_work("agent-1")
```

### Pattern 2: Concurrent Tasks
```python
# Multiple agents work simultaneously
agents = []
for i, task in enumerate(tasks):
    workspace = git_manager.create_worktree(f"agent-{i}")
    agent = Agent(workspace)
    agents.append((f"agent-{i}", agent, task))

# Each works in own worktree - no conflicts during execution

# Merge sequentially after completion
for agent_id, _, _ in agents:
    merge_result = git_manager.merge_agent_work(agent_id)
    if merge_result['status'] == 'conflicts':
        # Handle conflicts
        resolve_conflicts(merge_result['conflicts'])
```

### Pattern 3: Retry with Rollback
```python
agent_id = "agent-retry"
workspace = git_manager.create_worktree(agent_id)

try:
    result = agent.run("Complex refactor")
    if not result.success:
        # Bad result - rollback
        git_manager.remove_worktree(agent_id, keep_branch=False)
        
        # Try different approach
        workspace = git_manager.create_worktree(f"{agent_id}-v2")
        result = agent.run("Complex refactor (different approach)")
except Exception as e:
    # Error - keep worktree for debugging
    git_manager.remove_worktree(agent_id, keep_branch=True)
    raise
```

## Configuration

```python
worktree_config = {
    'enabled': True,
    'base_branch': 'main',
    'branch_prefix': 'agent/',
    'cleanup_policy': {
        'on_merge': True,
        'on_error': False,
        'on_session_end': True,
        'keep_branch': False
    },
    'sparse_checkout': False,  # For large repos
    'auto_commit': True,
    'commit_message_template': '[{agent_id}] {action}'
}
```

## Acceptance Criteria

- [ ] Can create worktree per agent
- [ ] Each worktree on unique branch
- [ ] Concurrent worktree creation safe (locking)
- [ ] Agent changes committed automatically
- [ ] Merge detects conflicts correctly
- [ ] Cleanup removes worktrees
- [ ] Branch deletion configurable
- [ ] Sparse checkout works for large repos
- [ ] Git operations don't fail due to locks
- [ ] Documentation covers worktree patterns
- [ ] Tests cover concurrent creation
- [ ] Tests cover merge conflicts

## Dependencies

- None (foundational)

## Estimated Effort

Medium (5 days)

## Trade-offs

### Advantages
✅ Built-in version control  
✅ Automatic conflict detection  
✅ Easy rollback  
✅ Audit trail  
✅ Lightweight (shared .git)  

### Disadvantages
⚠️ Shared .git can have lock contention  
⚠️ Storage overhead for large repos  
⚠️ Requires git knowledge  
⚠️ Cleanup complexity  

### When to Use
- **DO use** when:
  - You want version control per agent
  - Merge conflict detection valuable
  - Repository <100MB
  - Running <10 concurrent agents

- **DON'T use** when:
  - Repository very large (>1GB)
  - Running 50+ concurrent agents
  - Don't want git in the workflow
  - Need truly independent git history

### Alternative
For simpler use cases, regular directory isolation works fine:
```python
# Just copy the workspace
workspace = base_workspace / f"agent_{agent_id}"
shutil.copytree(base_workspace, workspace)
```

## Future Enhancements

- Git sparse checkout optimization
- Automatic conflict resolution (simple cases)
- Worktree templates (start from specific state)
- Branch archiving (keep history without branches)
- Multi-repository support
