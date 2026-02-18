# Universal Agent System - Sandboxed Environment Strategy

**Critical Issue**: Many agent environments are sandboxed with restricted file system access  
**Impact**: Current file-based architecture (symlinks, local configs) won't work  
**Solution**: Hybrid architecture supporting both local and sandboxed modes

---

## 🚨 The Sandboxing Problem

### What is a Sandboxed Agent Environment?

Sandboxed environments have:
- ❌ **No home directory access** - Can't read/write to `~/.agent/`, `~/.gemini/`
- ❌ **No persistent storage** - State resets between sessions
- ❌ **Limited file system** - May only access specific directories
- ❌ **No system modifications** - Can't install packages or create symlinks
- ❌ **Restricted network** - May have limited external access
- ❌ **Isolated per session** - Each invocation is a fresh environment

### Common Sandboxed Scenarios

| Environment | Access Level | Persistence | Config Access |
|-------------|--------------|-------------|---------------|
| **Claude.ai (web)** | Sandboxed workspace only | Session-scoped | None |
| **Claude Code (container)** | Limited filesystem | Container-scoped | Mount-based |
| **GitHub Actions** | Runner workspace | Job-scoped | Repository only |
| **Cloud IDEs** | Project directory | Session-scoped | Project config |
| **Browser agents** | Virtual filesystem | Memory only | API-injected |
| **Lambda/Functions** | Temp directory | Invocation-scoped | Environment vars |

### What Breaks in Current System?

```bash
# ❌ BREAKS: File system dependencies
~/.agent/AGENTS.md                    # Not accessible
~/.gemini/antigravity/skills/         # Not accessible
ln -s ~/.agent/skills ~/.gemini/...   # Symlinks fail

# ❌ BREAKS: Session persistence
~/.agent/state/session-abc123.json    # Lost after session
~/.agent/logs/audit.log               # No persistent logs

# ❌ BREAKS: Shared state
~/.agent/ledgers/task_ledger.json     # No shared access
git config --global user.name         # No global config

# ❌ BREAKS: Provider auto-detection
ls ~/.gemini                          # Directory doesn't exist
ps aux | grep gemini                  # Can't see processes
```

---

## 🏗️ Sandboxed-Compatible Architecture

### Core Principles

1. **API-First**: All resources accessible via HTTP/WebSocket API
2. **Stateless Operations**: Agent doesn't rely on local state
3. **Context Injection**: All configuration passed in request context
4. **Remote State**: Persistent state stored in external service
5. **Fallback Strategy**: Gracefully degrade if services unavailable

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Sandboxed Agent                            │
│  (No home directory, no persistent storage)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ All communication via API
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Universal Agent Service (Cloud)                 │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Config    │  │    Skills    │  │    State     │      │
│  │   API       │  │    Registry  │  │    Service   │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Audit     │  │    Lock      │  │   Workflow   │      │
│  │   Service   │  │    Service   │  │   Engine     │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ Persistent storage
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          Storage Layer (PostgreSQL, S3, Redis)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation: Hybrid VFS

The VFS needs to support **both local and remote** backends:

```python
# ~/.agent/core/vfs_hybrid.py
"""
Hybrid VFS supporting both local and sandboxed environments
"""
import os
from typing import Optional
from dataclasses import dataclass
import httpx
import json

@dataclass
class VFSConfig:
    """VFS configuration - can be injected or loaded"""
    mode: str  # 'local' or 'remote'
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    cache_enabled: bool = True
    
    @classmethod
    def auto_detect(cls):
        """Auto-detect if running in sandboxed environment"""
        # Check if home directory is accessible
        try:
            home = Path.home()
            agent_dir = home / '.agent'
            if agent_dir.exists() and os.access(agent_dir, os.W_OK):
                return cls(mode='local')
        except:
            pass
        
        # Sandboxed - use remote API
        api_url = os.getenv('AGENT_API_URL', 'https://api.agent.dev')
        api_key = os.getenv('AGENT_API_KEY')
        
        return cls(mode='remote', api_url=api_url, api_key=api_key)

class RemoteVFSBackend:
    """Remote backend using HTTP API"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.client = httpx.AsyncClient(
            base_url=api_url,
            headers={'Authorization': f'Bearer {api_key}'}
        )
    
    async def read(self, path: str) -> bytes:
        """Read from remote VFS"""
        response = await self.client.get(f'/vfs/read', params={'path': path})
        response.raise_for_status()
        return response.content
    
    async def write(self, path: str, content: bytes):
        """Write to remote VFS"""
        response = await self.client.post(
            f'/vfs/write',
            params={'path': path},
            content=content
        )
        response.raise_for_status()
    
    async def exists(self, path: str) -> bool:
        """Check if path exists"""
        response = await self.client.get(f'/vfs/exists', params={'path': path})
        return response.json()['exists']
    
    async def list(self, path: str) -> list:
        """List directory contents"""
        response = await self.client.get(f'/vfs/list', params={'path': path})
        return response.json()['items']
    
    async def resolve_skill(self, skill_name: str, provider: str = None) -> str:
        """Resolve skill location"""
        response = await self.client.get(
            f'/vfs/resolve-skill',
            params={'skill': skill_name, 'provider': provider}
        )
        return response.json()['path']

class HybridVFS:
    """VFS that works in both local and sandboxed environments"""
    
    def __init__(self, config: Optional[VFSConfig] = None):
        if config is None:
            config = VFSConfig.auto_detect()
        
        self.config = config
        
        if config.mode == 'local':
            from vfs import UniversalVFS
            self.backend = UniversalVFS()
        else:
            self.backend = RemoteVFSBackend(config.api_url, config.api_key)
    
    async def read(self, path: str, **kwargs) -> bytes:
        """Read - works in any environment"""
        return await self.backend.read(path)
    
    async def write(self, path: str, content: bytes):
        """Write - works in any environment"""
        return await self.backend.write(path, content)
    
    async def exists(self, path: str) -> bool:
        """Check existence - works in any environment"""
        return await self.backend.exists(path)
    
    async def list(self, path: str) -> list:
        """List - works in any environment"""
        return await self.backend.list(path)
    
    async def resolve_skill(self, skill_name: str, provider: str = None) -> str:
        """Resolve skill - works in any environment"""
        return await self.backend.resolve_skill(skill_name, provider)
    
    def is_sandboxed(self) -> bool:
        """Check if running in sandboxed mode"""
        return self.config.mode == 'remote'

# Usage example
async def example():
    # Auto-detects environment
    vfs = HybridVFS()
    
    if vfs.is_sandboxed():
        print("Running in sandboxed mode - using remote API")
    else:
        print("Running in local mode - using file system")
    
    # Same API works in both modes
    content = await vfs.read("vfs://agent/docs/AGENTS.md")
    skill_path = await vfs.resolve_skill("orchestrator")
```

---

## 🌐 Universal Agent Service API

### Core API Endpoints

```yaml
# OpenAPI specification
openapi: 3.0.0
info:
  title: Universal Agent Service API
  version: 1.0.0

servers:
  - url: https://api.agent.dev

security:
  - BearerAuth: []

paths:
  # Configuration API
  /config/protocols:
    get:
      summary: Get universal protocols (AGENTS.md content)
      responses:
        '200':
          description: Protocol document
          content:
            text/markdown:
              schema:
                type: string
  
  /config/sop:
    get:
      summary: Get SOP compliance checklist
      responses:
        '200':
          description: SOP checklist
  
  /config/provider/{provider}:
    get:
      summary: Get provider-specific configuration
      parameters:
        - name: provider
          in: path
          required: true
          schema:
            type: string
            enum: [gemini, claude, opencode, cursor]
  
  # VFS API
  /vfs/read:
    get:
      summary: Read from virtual file system
      parameters:
        - name: path
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: File content
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
  
  /vfs/write:
    post:
      summary: Write to virtual file system
      parameters:
        - name: path
          in: query
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/octet-stream:
            schema:
              type: string
              format: binary
  
  /vfs/resolve-skill:
    get:
      summary: Resolve skill location
      parameters:
        - name: skill
          in: query
          required: true
        - name: provider
          in: query
          required: false
  
  # Skills API
  /skills/list:
    get:
      summary: List available skills
      parameters:
        - name: provider
          in: query
          required: false
  
  /skills/{skill}/manifest:
    get:
      summary: Get skill manifest
  
  /skills/{skill}/content:
    get:
      summary: Get skill content (SKILL.md)
  
  # State API
  /state/session:
    post:
      summary: Create new session
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                provider:
                  type: string
                agent_id:
                  type: string
                task_id:
                  type: string
    
    put:
      summary: Update session state
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                session_id:
                  type: string
                state:
                  type: object
    
    get:
      summary: Get session state
      parameters:
        - name: session_id
          in: query
  
  # Coordination API
  /coordination/lock:
    post:
      summary: Acquire distributed lock
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                resource:
                  type: string
                timeout:
                  type: integer
    
    delete:
      summary: Release distributed lock
      parameters:
        - name: lock_id
          in: query
  
  /coordination/events:
    post:
      summary: Publish event
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                channel:
                  type: string
                event:
                  type: object
  
  /coordination/events/subscribe:
    get:
      summary: Subscribe to event stream (WebSocket)
      parameters:
        - name: channel
          in: query
  
  # Audit API
  /audit/log:
    post:
      summary: Log audit event
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                event_type:
                  type: string
                session_id:
                  type: string
                data:
                  type: object
    
    get:
      summary: Query audit logs
      parameters:
        - name: session_id
          in: query
        - name: start_time
          in: query
        - name: end_time
          in: query

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
```

---

## 📦 Provider-Specific Integration

### 1. Claude.ai (Web Interface)

**Challenge**: Completely sandboxed, no file system access

**Solution**: API key in system prompt

```markdown
<!-- System prompt injection -->
You are operating in a sandboxed environment. To access the Universal Agent System:

1. Use the Agent API: https://api.agent.dev
2. Your API key: $AGENT_API_KEY
3. Your session: $AGENT_SESSION_ID

Before ANY task, initialize:
```python
from agent_client import AgentClient
client = AgentClient(api_key=os.getenv('AGENT_API_KEY'))

# Get protocols
protocols = await client.get_protocols()

# Get your session state
session = await client.get_session(os.getenv('AGENT_SESSION_ID'))

# Resolve skills
orchestrator = await client.resolve_skill('orchestrator')
```

All resources are accessed via API, not file system.
```

### 2. Claude Code (Container)

**Challenge**: Limited persistence, isolated container

**Solution**: Mount points + API hybrid

```yaml
# docker-compose.yml for Claude Code
version: '3.8'
services:
  claude-code:
    image: claude-code:latest
    environment:
      - AGENT_API_URL=https://api.agent.dev
      - AGENT_API_KEY=${AGENT_API_KEY}
      - AGENT_MODE=hybrid  # Use API for shared resources, local for session
    volumes:
      # Mount read-only protocol docs
      - ./protocols:/mnt/protocols:ro
      # Session-specific workspace
      - ./workspace:/workspace:rw
    command: >
      --config /mnt/protocols/AGENTS.md
      --api-url https://api.agent.dev
```

**Code configuration**:
```python
# Auto-detect hybrid mode
config = VFSConfig.auto_detect()
if os.path.exists('/mnt/protocols'):
    # Use mounted protocols as read-only cache
    config.mount_cache = '/mnt/protocols'

vfs = HybridVFS(config)
```

### 3. GitHub Actions / CI/CD

**Challenge**: Ephemeral runners, no persistence between jobs

**Solution**: API-only mode with job artifacts

```yaml
# .github/workflows/agent-task.yml
name: Agent Task Execution
on: [workflow_dispatch]

jobs:
  agent-task:
    runs-on: ubuntu-latest
    steps:
      - name: Setup Agent Client
        run: |
          pip install agent-client
          export AGENT_API_URL=https://api.agent.dev
          export AGENT_API_KEY=${{ secrets.AGENT_API_KEY }}
      
      - name: Initialize Session
        run: |
          SESSION_ID=$(agent-cli session create \
            --provider github-actions \
            --task-id ${{ github.run_id }})
          echo "SESSION_ID=$SESSION_ID" >> $GITHUB_ENV
      
      - name: Execute Task
        run: |
          agent-cli task execute \
            --session $SESSION_ID \
            --task "${{ github.event.inputs.task }}"
      
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: task-results
          path: /tmp/agent-output/
```

### 4. Browser-Based Agents

**Challenge**: No file system at all, browser sandbox only

**Solution**: Pure API mode with WebSocket

```javascript
// Browser agent client
class BrowserAgentClient {
  constructor(apiUrl, apiKey) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
    this.ws = null;
  }
  
  async initialize() {
    // Create session
    const response = await fetch(`${this.apiUrl}/state/session`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider: 'browser',
        agent_id: this.getAgentId()
      })
    });
    
    this.sessionId = (await response.json()).session_id;
    
    // Connect WebSocket for real-time updates
    this.ws = new WebSocket(
      `${this.apiUrl.replace('http', 'ws')}/coordination/events/subscribe?channel=agent.${this.sessionId}`
    );
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleEvent(data);
    };
  }
  
  async getProtocols() {
    const response = await fetch(`${this.apiUrl}/config/protocols`, {
      headers: {'Authorization': `Bearer ${this.apiKey}`}
    });
    return await response.text();
  }
  
  async resolveSkill(skillName, provider = null) {
    const params = new URLSearchParams({skill: skillName});
    if (provider) params.append('provider', provider);
    
    const response = await fetch(
      `${this.apiUrl}/vfs/resolve-skill?${params}`,
      {headers: {'Authorization': `Bearer ${this.apiKey}`}}
    );
    return await response.json();
  }
  
  async acquireLock(resource, timeout = 30) {
    const response = await fetch(`${this.apiUrl}/coordination/lock`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({resource, timeout})
    });
    return await response.json();
  }
  
  // Store state in remote service (not localStorage!)
  async saveState(state) {
    await fetch(`${this.apiUrl}/state/session`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: this.sessionId,
        state: state
      })
    });
  }
}

// Usage in browser agent
const client = new BrowserAgentClient(
  'https://api.agent.dev',
  'your-api-key'
);

await client.initialize();
const protocols = await client.getProtocols();
console.log('Loaded protocols:', protocols);
```

---

## 🔐 Security & Authentication

### API Authentication

```python
# Client library with authentication
class AgentClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('AGENT_API_KEY')
        if not self.api_key:
            raise ValueError("AGENT_API_KEY required")
        
        self.client = httpx.AsyncClient(
            base_url=os.getenv('AGENT_API_URL', 'https://api.agent.dev'),
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
    
    async def get_protocols(self) -> str:
        response = await self.client.get('/config/protocols')
        response.raise_for_status()
        return response.text
    
    # ... other methods
```

### Key Management

**For Production**:
```bash
# Environment-based secrets
export AGENT_API_KEY="sk-..."  # Injected by platform

# Or use secret managers
# AWS Secrets Manager
AGENT_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id agent-api-key \
  --query SecretString \
  --output text)

# HashiCorp Vault
AGENT_API_KEY=$(vault kv get -field=api_key secret/agent)
```

**For Development**:
```bash
# .env file (never commit!)
AGENT_API_KEY=sk-dev-...
AGENT_API_URL=http://localhost:8080
```

---

## 🚀 Migration Strategy

### Phase 1: Add API Service (Week 1-2)

1. **Deploy API service** with core endpoints
2. **Keep local mode working** - no breaking changes
3. **Add hybrid VFS** that can use either backend
4. **Test with one sandboxed provider** (e.g., GitHub Actions)

### Phase 2: Update Client Libraries (Week 3-4)

1. **Create `agent-client` package**
   ```bash
   pip install agent-client
   npm install @agent/client
   ```

2. **Update documentation** for sandboxed usage

3. **Add auto-detection** in all tools

### Phase 3: Provider Integration (Week 5-8)

1. **Update each provider** with API support
2. **Add configuration injection** for sandboxed environments
3. **Test thoroughly** in actual sandboxed environments
4. **Document provider-specific setup**

### Phase 4: Optimize & Monitor (Ongoing)

1. **Add caching layers** to reduce API calls
2. **Monitor API performance** and costs
3. **Collect usage metrics**
4. **Iterate based on feedback**

---

## 📊 Comparison: Local vs Sandboxed

| Feature | Local Mode | Sandboxed Mode | Hybrid Mode |
|---------|-----------|----------------|-------------|
| **File Access** | Direct | API only | Cached + API |
| **Performance** | Fastest | Slower (network) | Medium |
| **Setup** | Complex | Simple | Auto-detect |
| **Cost** | Free | API costs | Variable |
| **Offline** | Yes | No | Fallback |
| **Shared State** | Limited | Full | Full |
| **Multi-Agent** | Race conditions | Coordinated | Coordinated |

---

## 💡 Best Practices

### 1. Design for Sandboxing from the Start

```python
# ❌ BAD: Assumes local file system
def get_protocols():
    return Path.home() / '.agent' / 'AGENTS.md').read_text()

# ✅ GOOD: Works in any environment
async def get_protocols(vfs: HybridVFS):
    return await vfs.read('vfs://agent/AGENTS.md')
```

### 2. Use Environment Detection

```python
# Auto-detect and adapt
config = VFSConfig.auto_detect()
if config.mode == 'remote':
    print("Running in sandboxed mode")
    # Adjust behavior accordingly
```

### 3. Fail Gracefully

```python
# Fallback strategy
try:
    protocols = await vfs.read('vfs://agent/AGENTS.md')
except Exception as e:
    # Use embedded copy as fallback
    protocols = EMBEDDED_PROTOCOLS
```

### 4. Cache Aggressively

```python
# Cache remote resources locally when possible
@lru_cache(maxsize=100)
async def get_skill(skill_name: str):
    return await vfs.read(f'vfs://skills/{skill_name}/SKILL.md')
```

### 5. Minimize API Calls

```python
# ❌ BAD: Multiple API calls
protocol = await get_protocols()
sop = await get_sop()
skill = await get_skill('orchestrator')

# ✅ GOOD: Batch request
resources = await client.get_batch([
    'protocols',
    'sop',
    'skills/orchestrator'
])
```

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Works in Claude.ai web interface
- ✅ Works in containerized Claude Code
- ✅ Works in GitHub Actions
- ✅ Works in local development
- ✅ Auto-detects environment
- ✅ Graceful fallbacks

### Performance Requirements
- ✅ < 100ms API response time (P95)
- ✅ < 2s initial session setup
- ✅ Effective caching (>80% hit rate)
- ✅ < 1000 API calls per session

### Cost Requirements
- ✅ < $0.01 per agent session (API costs)
- ✅ Self-hosting option available
- ✅ Offline mode for development

---

## 🏁 Conclusion

**Key Insight**: A truly universal agent system must support **both local and sandboxed** environments.

**The Solution**:
1. **API-first architecture** - Everything accessible via HTTP
2. **Hybrid VFS** - Automatically uses local or remote backend
3. **Client libraries** - Same code works everywhere
4. **Auto-detection** - No manual configuration
5. **Progressive enhancement** - Works with or without API

**Implementation Priority**:
1. Start with API service (core endpoints)
2. Add hybrid VFS support
3. Update one provider to test (GitHub Actions is easiest)
4. Roll out to other providers
5. Optimize and monitor

This approach ensures your universal agent system truly works **everywhere**, from a developer's laptop to a browser sandbox to a cloud function.

---

**Next Steps**: 
1. Deploy minimal API service with /config and /vfs endpoints
2. Test with one sandboxed provider (e.g., GitHub Actions workflow)
3. Validate before full rollout
