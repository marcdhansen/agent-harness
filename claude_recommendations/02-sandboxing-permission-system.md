---
title: "Implement Multi-Layer Sandboxing and Permission System"
labels: critical, security, enhancement
priority: P0
---

## Problem Statement

Current implementation lacks clear sandboxing strategy for agent execution:
- No isolation for bash commands (potential security risk)
- No permission model for file system access
- Unclear how to prevent dangerous operations (e.g., `rm -rf /`)
- No resource limits (CPU, memory, time)
- Agents could potentially interfere with each other or system

## Proposed Solution

Implement multi-layer isolation:

### Layer 1: Lightweight Container Isolation (Colima/Lima)
```python
class ColimaSandbox:
    """Container-based isolation for high-risk operations"""
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.ensure_runtime_running()  # Colima or Lima
        
    def execute_bash(self, command: str, timeout: int = 30) -> str:
        """Run bash in isolated container"""
        docker_cmd = [
            'docker', 'run', '--rm',
            '-v', f'{self.workspace}:/workspace',
            '-w', '/workspace',
            '--network', 'none',  # No network by default
            '--memory', '512m',
            '--cpus', '0.5',
            'python:3.11-slim',
            'bash', '-c', command
        ]
        # Execute with timeout and resource limits
```

### Layer 2: Path-Based Permission System
```python
class PermissionManager:
    """Track and enforce directory access permissions"""
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.granted_paths = {workspace_root}
        
    def request_permission(self, path: str) -> bool:
        """Human-in-loop permission request"""
        abs_path = Path(path).resolve()
        
        if self._is_granted(abs_path):
            return True
            
        # Ask user for permission
        if self._ask_user(f"Grant access to {abs_path}?"):
            self.granted_paths.add(abs_path)
            return True
        return False
        
    def validate_path(self, path: str):
        """Validate before any file operation"""
        if not self._is_granted(path):
            raise PermissionError(f"Access denied: {path}")
```

### Layer 3: Session Isolation
```python
class IsolatedAgentSession:
    """Each agent gets isolated resources"""
    def __init__(self, session_id: str, base_workspace: Path):
        self.session_id = session_id
        self.workspace = base_workspace / f"agent_{session_id}"
        self.sandbox = ColimaSandbox(self.workspace)
        self.permissions = PermissionManager(self.workspace)
```

## Implementation Details

1. **Choose lightweight runtime**:
   - Primary: Colima (drop-in Docker replacement)
   - Alternative: Lima + nerdctl
   - Fallback: OrbStack (paid but excellent)

2. **Implement ColimaSandbox class**:
   - Container lifecycle management
   - Resource limits (CPU, memory, timeout)
   - Network isolation (opt-in only)
   - Volume mounting

3. **Implement PermissionManager**:
   - Path validation
   - Permission inheritance (grant parent → includes children)
   - Human-in-loop approval
   - Session-based permission storage
   - Audit logging

4. **Implement IsolatedAgentSession**:
   - Unique workspace per agent
   - Cleanup on session end
   - Concurrent session support

5. **Integrate with existing tools**:
   - `bash` tool uses ColimaSandbox
   - `read/write/edit` tools use PermissionManager
   - Tools validate paths before execution

6. **Add configuration options**:
   - Choose runtime (colima/lima/docker)
   - Default resource limits
   - Network access policy
   - Auto-cleanup settings

## Acceptance Criteria

- [ ] Bash commands execute in isolated containers
- [ ] Resource limits enforced (CPU, memory, time)
- [ ] Network access disabled by default
- [ ] Permission system prevents unauthorized file access
- [ ] Human-in-loop permission requests work
- [ ] Multiple agents can run concurrently without interference
- [ ] Colima/Lima auto-starts if not running
- [ ] Permission grants persisted per session
- [ ] Audit log tracks all permission grants
- [ ] Documentation covers security model
- [ ] Tests cover permission denial and container isolation

## Dependencies

- None (can implement independently)
- Complements: Issue #7 (Concurrent Execution)

## Estimated Effort

Large (2 weeks)

## References

- [Colima GitHub](https://github.com/abiosoft/colima)
- [Lima GitHub](https://github.com/lima-vm/lima)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

## Notes

For Intel Mac users, Docker Desktop is too heavy. Recommend Colima as default with Lima as alternative. Both are significantly lighter (~500MB vs 2-4GB).
