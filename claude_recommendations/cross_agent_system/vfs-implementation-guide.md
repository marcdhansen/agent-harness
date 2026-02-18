# Virtual File System (VFS) - Detailed Implementation Guide

**Purpose**: Replace OS-level symlinks with a portable, testable Virtual File System  
**Priority**: CRITICAL - Foundation for all other improvements  
**Estimated Effort**: 2-3 weeks for core implementation

---

## 🎯 Design Goals

1. **Cross-Platform**: Works on Windows, macOS, Linux without admin privileges
2. **Testable**: Easy to mock and test in isolation
3. **Performant**: Caching and lazy loading for efficiency
4. **Versioned**: Support multiple versions of same resource
5. **Network-Capable**: Can load resources from remote locations
6. **Atomic**: Updates are transactional and rollback-safe

---

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Applications                        │
│  (Gemini, Claude, OpenCode, Cursor)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   VFS API Layer                              │
│  read(), write(), resolve_skill(), mount()                  │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
    ┌─────────┐    ┌─────────┐   ┌──────────┐
    │  Cache  │    │Resolver │   │ Backends │
    │  Layer  │    │ Engine  │   │ (FS/HTTP)│
    └─────────┘    └─────────┘   └──────────┘
                         │
                         ▼
               ┌──────────────────┐
               │  Physical Storage │
               │  - Local Files   │
               │  - Remote URLs   │
               │  - Git Repos     │
               └──────────────────┘
```

---

## 🏗️ Core Components

### 1. VFS Core (`~/.agent/core/vfs.py`)

```python
"""
Virtual File System for Universal Agent Framework
Replaces OS-level symlinks with cross-platform abstraction
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Union, List
from functools import lru_cache
import asyncio
from urllib.parse import urlparse


@dataclass
class VFSMount:
    """VFS mount point configuration"""
    virtual_path: str
    physical_path: str
    provider: str = "universal"
    version: Optional[str] = None
    read_only: bool = False
    cache_ttl: int = 300  # 5 minutes default
    mounted_at: float = None
    
    def __post_init__(self):
        if self.mounted_at is None:
            self.mounted_at = time.time()
    
    @property
    def is_expired(self) -> bool:
        """Check if mount cache is expired"""
        return time.time() - self.mounted_at > self.cache_ttl


@dataclass
class VFSEntry:
    """VFS entry metadata"""
    path: str
    content_hash: str
    size: int
    modified_at: float
    cached_at: float
    provider: str


class VFSCache:
    """LRU cache with TTL support"""
    
    def __init__(self, maxsize: int = 1000, default_ttl: int = 300):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: Dict[str, tuple] = {}  # key -> (value, expires_at)
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None
        
        value, expires_at = self._cache[key]
        
        if time.time() > expires_at:
            # Expired, remove it
            self._remove(key)
            return None
        
        # Update access order (LRU)
        self._access_order.remove(key)
        self._access_order.append(key)
        
        return value
    
    def set(self, key: str, value: any, ttl: Optional[int] = None):
        """Set cached value with TTL"""
        if ttl is None:
            ttl = self.default_ttl
        
        expires_at = time.time() + ttl
        
        # Evict if at capacity
        if len(self._cache) >= self.maxsize and key not in self._cache:
            lru_key = self._access_order[0]
            self._remove(lru_key)
        
        self._cache[key] = (value, expires_at)
        
        if key not in self._access_order:
            self._access_order.append(key)
    
    def _remove(self, key: str):
        """Remove key from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def clear(self):
        """Clear all cached entries"""
        self._cache.clear()
        self._access_order.clear()
    
    def stats(self) -> dict:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "max_size": self.maxsize,
            "utilization": len(self._cache) / self.maxsize
        }


class VFSBackend:
    """Base class for VFS storage backends"""
    
    async def read(self, path: str) -> bytes:
        raise NotImplementedError
    
    async def write(self, path: str, content: bytes):
        raise NotImplementedError
    
    async def exists(self, path: str) -> bool:
        raise NotImplementedError
    
    async def list(self, path: str) -> List[str]:
        raise NotImplementedError


class LocalFSBackend(VFSBackend):
    """Local file system backend"""
    
    async def read(self, path: str) -> bytes:
        return Path(path).read_bytes()
    
    async def write(self, path: str, content: bytes):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(content)
    
    async def exists(self, path: str) -> bool:
        return Path(path).exists()
    
    async def list(self, path: str) -> List[str]:
        return [str(p) for p in Path(path).iterdir()]


class HTTPBackend(VFSBackend):
    """HTTP/HTTPS backend for remote resources"""
    
    def __init__(self):
        import aiohttp
        self.session = aiohttp.ClientSession()
    
    async def read(self, url: str) -> bytes:
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.read()
    
    async def exists(self, url: str) -> bool:
        try:
            async with self.session.head(url) as response:
                return response.status == 200
        except:
            return False
    
    async def close(self):
        await self.session.close()


class GitBackend(VFSBackend):
    """Git repository backend"""
    
    def __init__(self, cache_dir: Path = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".agent" / "git-cache"
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def read(self, git_url: str) -> bytes:
        # Parse git URL: git://repo.git@branch/path/to/file
        repo_url, ref_and_path = git_url.split('@')
        ref, file_path = ref_and_path.split('/', 1)
        
        # Clone or update repo
        repo_hash = hashlib.md5(repo_url.encode()).hexdigest()
        repo_dir = self.cache_dir / repo_hash
        
        if not repo_dir.exists():
            await self._clone_repo(repo_url, repo_dir)
        else:
            await self._update_repo(repo_dir)
        
        # Checkout ref
        await self._checkout_ref(repo_dir, ref)
        
        # Read file
        file_full_path = repo_dir / file_path
        return file_full_path.read_bytes()
    
    async def _clone_repo(self, repo_url: str, dest: Path):
        """Clone git repository"""
        import subprocess
        subprocess.run(
            ["git", "clone", repo_url, str(dest)],
            check=True,
            capture_output=True
        )
    
    async def _update_repo(self, repo_dir: Path):
        """Update git repository"""
        import subprocess
        subprocess.run(
            ["git", "-C", str(repo_dir), "fetch"],
            check=True,
            capture_output=True
        )
    
    async def _checkout_ref(self, repo_dir: Path, ref: str):
        """Checkout specific ref"""
        import subprocess
        subprocess.run(
            ["git", "-C", str(repo_dir), "checkout", ref],
            check=True,
            capture_output=True
        )


class UniversalVFS:
    """Virtual File System for cross-agent resource access"""
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path.home() / ".agent" / "vfs-config.json"
        
        self.config_path = config_path
        self.mounts: Dict[str, VFSMount] = {}
        self.cache = VFSCache(maxsize=1000)
        self.backends = {
            "file": LocalFSBackend(),
            "http": HTTPBackend(),
            "https": HTTPBackend(),
            "git": GitBackend(),
        }
        
        # Load configuration
        if config_path.exists():
            self.load_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default VFS configuration"""
        default_mounts = [
            VFSMount(
                virtual_path="vfs://agent/docs",
                physical_path=str(Path.home() / ".agent" / "docs"),
                provider="universal"
            ),
            VFSMount(
                virtual_path="vfs://agent/skills",
                physical_path=str(Path.home() / ".gemini" / "antigravity" / "skills"),
                provider="universal"
            ),
            VFSMount(
                virtual_path="vfs://agent/workflows",
                physical_path=str(Path.home() / ".gemini" / "antigravity" / "global_workflows"),
                provider="universal"
            ),
        ]
        
        for mount in default_mounts:
            self.mounts[mount.virtual_path] = mount
        
        self.save_config()
    
    def load_config(self):
        """Load VFS configuration from file"""
        config_data = json.loads(self.config_path.read_text())
        for mount_data in config_data.get("mounts", []):
            mount = VFSMount(**mount_data)
            self.mounts[mount.virtual_path] = mount
    
    def save_config(self):
        """Save VFS configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        config_data = {
            "mounts": [asdict(m) for m in self.mounts.values()]
        }
        self.config_path.write_text(json.dumps(config_data, indent=2))
    
    def mount(self, virtual_path: str, physical_path: str, **kwargs):
        """Mount a physical location to virtual path"""
        mount = VFSMount(
            virtual_path=virtual_path,
            physical_path=physical_path,
            **kwargs
        )
        self.mounts[virtual_path] = mount
        self.save_config()
    
    def unmount(self, virtual_path: str):
        """Unmount a virtual path"""
        if virtual_path in self.mounts:
            del self.mounts[virtual_path]
            self.save_config()
    
    async def read(self, virtual_path: str, use_cache: bool = True) -> bytes:
        """Read from virtual path"""
        # Check cache first
        if use_cache:
            cached = self.cache.get(virtual_path)
            if cached is not None:
                return cached
        
        # Resolve to physical path
        physical_path = self._resolve(virtual_path)
        if physical_path is None:
            raise FileNotFoundError(f"Virtual path not mounted: {virtual_path}")
        
        # Determine backend
        backend = self._get_backend(physical_path)
        
        # Read content
        content = await backend.read(physical_path)
        
        # Cache it
        if use_cache:
            self.cache.set(virtual_path, content)
        
        return content
    
    async def write(self, virtual_path: str, content: bytes):
        """Write to virtual path"""
        mount = self._find_mount(virtual_path)
        if mount is None:
            raise FileNotFoundError(f"Virtual path not mounted: {virtual_path}")
        
        if mount.read_only:
            raise PermissionError(f"Mount is read-only: {virtual_path}")
        
        # Resolve to physical path
        physical_path = self._resolve(virtual_path)
        
        # Determine backend
        backend = self._get_backend(physical_path)
        
        # Write content
        await backend.write(physical_path, content)
        
        # Invalidate cache
        if virtual_path in self.cache._cache:
            self.cache._remove(virtual_path)
    
    async def exists(self, virtual_path: str) -> bool:
        """Check if virtual path exists"""
        try:
            physical_path = self._resolve(virtual_path)
            if physical_path is None:
                return False
            
            backend = self._get_backend(physical_path)
            return await backend.exists(physical_path)
        except:
            return False
    
    async def list(self, virtual_path: str) -> List[str]:
        """List contents of virtual directory"""
        physical_path = self._resolve(virtual_path)
        if physical_path is None:
            return []
        
        backend = self._get_backend(physical_path)
        physical_items = await backend.list(physical_path)
        
        # Convert back to virtual paths
        base_physical = str(Path(physical_path))
        base_virtual = virtual_path.rstrip('/')
        
        virtual_items = []
        for physical_item in physical_items:
            relative = Path(physical_item).relative_to(base_physical)
            virtual_item = f"{base_virtual}/{relative}"
            virtual_items.append(virtual_item)
        
        return virtual_items
    
    def _find_mount(self, virtual_path: str) -> Optional[VFSMount]:
        """Find mount point for virtual path"""
        # Find longest matching prefix
        best_match = None
        best_length = 0
        
        for mount_path, mount in self.mounts.items():
            if virtual_path.startswith(mount_path):
                if len(mount_path) > best_length:
                    best_match = mount
                    best_length = len(mount_path)
        
        return best_match
    
    def _resolve(self, virtual_path: str) -> Optional[str]:
        """Resolve virtual path to physical path"""
        mount = self._find_mount(virtual_path)
        if mount is None:
            return None
        
        # Check if mount is expired and refresh if needed
        if mount.is_expired:
            # Reload configuration
            self.load_config()
            mount = self._find_mount(virtual_path)
        
        # Calculate relative path
        relative = virtual_path[len(mount.virtual_path):].lstrip('/')
        
        # Build physical path
        physical = str(Path(mount.physical_path) / relative)
        
        return physical
    
    def _get_backend(self, path: str) -> VFSBackend:
        """Get appropriate backend for path"""
        parsed = urlparse(path)
        
        if parsed.scheme in ('http', 'https'):
            return self.backends['http']
        elif parsed.scheme == 'git':
            return self.backends['git']
        else:
            return self.backends['file']
    
    async def resolve_skill(self, skill_name: str, provider: Optional[str] = None, 
                          version: Optional[str] = None) -> str:
        """Resolve skill location across providers"""
        search_paths = []
        
        # Provider-specific path
        if provider:
            search_paths.append(f"vfs://agent/skills/{provider}/{skill_name}")
        
        # Universal path
        search_paths.append(f"vfs://agent/skills/universal/{skill_name}")
        
        # Versioned path
        if version:
            search_paths.append(f"vfs://agent/skills/{skill_name}/{version}")
        
        # Fallback path
        search_paths.append(f"vfs://agent/skills/{skill_name}")
        
        for vpath in search_paths:
            if await self.exists(vpath):
                return vpath
        
        raise FileNotFoundError(f"Skill not found: {skill_name}")
    
    async def resolve_workflow(self, workflow_name: str) -> str:
        """Resolve workflow/command location"""
        vpath = f"vfs://agent/workflows/{workflow_name}.md"
        if await self.exists(vpath):
            return vpath
        
        raise FileNotFoundError(f"Workflow not found: {workflow_name}")
    
    def stats(self) -> dict:
        """Get VFS statistics"""
        return {
            "mounts": len(self.mounts),
            "cache": self.cache.stats(),
            "backends": list(self.backends.keys())
        }
    
    async def close(self):
        """Cleanup VFS resources"""
        if 'http' in self.backends:
            await self.backends['http'].close()


# Global VFS instance
_vfs_instance: Optional[UniversalVFS] = None


def get_vfs() -> UniversalVFS:
    """Get or create global VFS instance"""
    global _vfs_instance
    if _vfs_instance is None:
        _vfs_instance = UniversalVFS()
    return _vfs_instance


# Convenience functions
async def vfs_read(path: str, **kwargs) -> bytes:
    """Read from VFS"""
    vfs = get_vfs()
    return await vfs.read(path, **kwargs)


async def vfs_write(path: str, content: bytes):
    """Write to VFS"""
    vfs = get_vfs()
    return await vfs.write(path, content)


async def vfs_exists(path: str) -> bool:
    """Check if VFS path exists"""
    vfs = get_vfs()
    return await vfs.exists(path)
```

---

## 🔧 Usage Examples

### Example 1: Basic Mount and Read

```python
import asyncio
from pathlib import Path
from vfs import UniversalVFS

async def main():
    vfs = UniversalVFS()
    
    # Mount a directory
    vfs.mount(
        virtual_path="vfs://project/docs",
        physical_path="/Users/march/projects/myproject/docs",
        provider="project"
    )
    
    # Read a file
    content = await vfs.read("vfs://project/docs/README.md")
    print(content.decode())
    
    # List directory
    files = await vfs.list("vfs://project/docs")
    print(files)

asyncio.run(main())
```

### Example 2: Resolve Skills

```python
async def load_skill(skill_name: str, provider: str = None):
    vfs = UniversalVFS()
    
    try:
        # Resolve skill location
        skill_path = await vfs.resolve_skill(skill_name, provider)
        
        # Read skill manifest
        manifest_path = f"{skill_path}/SKILL.md"
        manifest = await vfs.read(manifest_path)
        
        print(f"Loaded skill from: {skill_path}")
        return manifest.decode()
        
    except FileNotFoundError as e:
        print(f"Skill not found: {e}")
        return None

# Usage
skill_content = await load_skill("orchestrator", provider="gemini")
```

### Example 3: Remote Resources

```python
async def load_remote_skill():
    vfs = UniversalVFS()
    
    # Mount remote HTTP resource
    vfs.mount(
        virtual_path="vfs://remote/skills",
        physical_path="https://skills.agent.dev/v1",
        provider="remote"
    )
    
    # Read remote skill
    skill = await vfs.read("vfs://remote/skills/orchestrator/v2.1.0/SKILL.md")
    print(skill.decode())

asyncio.run(load_remote_skill())
```

### Example 4: Git Repository

```python
async def load_from_git():
    vfs = UniversalVFS()
    
    # Mount git repository
    vfs.mount(
        virtual_path="vfs://git/skills",
        physical_path="git://github.com/user/skills-repo.git@main",
        provider="git"
    )
    
    # Read from git
    skill = await vfs.read("vfs://git/skills/custom-skill/SKILL.md")
    print(skill.decode())

asyncio.run(load_from_git())
```

---

## 🧪 Testing Strategy

### Unit Tests (`tests/test_vfs.py`)

```python
import pytest
from pathlib import Path
from vfs import UniversalVFS, VFSMount, VFSCache

@pytest.fixture
def temp_vfs(tmp_path):
    """Create temporary VFS instance"""
    config_path = tmp_path / "vfs-config.json"
    vfs = UniversalVFS(config_path=config_path)
    return vfs

@pytest.mark.asyncio
async def test_mount_and_read(temp_vfs, tmp_path):
    """Test mounting and reading"""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello VFS")
    
    # Mount
    temp_vfs.mount(
        virtual_path="vfs://test/files",
        physical_path=str(tmp_path)
    )
    
    # Read
    content = await temp_vfs.read("vfs://test/files/test.txt")
    assert content.decode() == "Hello VFS"

@pytest.mark.asyncio
async def test_cache_expiration(temp_vfs, tmp_path):
    """Test cache TTL"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Version 1")
    
    temp_vfs.mount(
        virtual_path="vfs://test/files",
        physical_path=str(tmp_path),
        cache_ttl=1  # 1 second TTL
    )
    
    # First read
    content1 = await temp_vfs.read("vfs://test/files/test.txt")
    assert content1.decode() == "Version 1"
    
    # Modify file
    test_file.write_text("Version 2")
    
    # Read from cache (should still be Version 1)
    content2 = await temp_vfs.read("vfs://test/files/test.txt")
    assert content2.decode() == "Version 1"
    
    # Wait for cache to expire
    await asyncio.sleep(1.5)
    
    # Read again (should be Version 2)
    content3 = await temp_vfs.read("vfs://test/files/test.txt")
    assert content3.decode() == "Version 2"

@pytest.mark.asyncio
async def test_skill_resolution(temp_vfs, tmp_path):
    """Test skill resolution"""
    # Create skill structure
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    
    skill_dir = skills_dir / "orchestrator"
    skill_dir.mkdir()
    
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("# Orchestrator Skill")
    
    # Mount
    temp_vfs.mount(
        virtual_path="vfs://agent/skills",
        physical_path=str(skills_dir)
    )
    
    # Resolve skill
    skill_path = await temp_vfs.resolve_skill("orchestrator")
    assert "orchestrator" in skill_path
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_workflow(temp_vfs, tmp_path):
    """Test complete workflow"""
    # Setup directory structure
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    
    docs_dir = agent_dir / "docs"
    docs_dir.mkdir()
    
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir()
    
    # Create files
    (docs_dir / "AGENTS.md").write_text("# Universal Agent")
    (skills_dir / "orchestrator" / "SKILL.md").write_text("# Orchestrator")
    
    # Mount
    temp_vfs.mount("vfs://agent/docs", str(docs_dir))
    temp_vfs.mount("vfs://agent/skills", str(skills_dir))
    
    # Test reads
    agents_content = await temp_vfs.read("vfs://agent/docs/AGENTS.md")
    assert "Universal Agent" in agents_content.decode()
    
    skill_path = await temp_vfs.resolve_skill("orchestrator")
    skill_content = await temp_vfs.read(f"{skill_path}/SKILL.md")
    assert "Orchestrator" in skill_content.decode()
```

---

## 🚀 Migration Guide

### Step 1: Install VFS Alongside Symlinks

```bash
# Install VFS module
pip install -e ~/.agent/core/

# Initialize VFS configuration
python -m vfs.cli init
```

### Step 2: Update Code to Use VFS

**Before (with symlinks):**
```python
# Old code using symlinks
skill_path = Path.home() / ".agent" / "skills" / "orchestrator"
skill_content = (skill_path / "SKILL.md").read_text()
```

**After (with VFS):**
```python
# New code using VFS
from vfs import get_vfs

vfs = get_vfs()
skill_path = await vfs.resolve_skill("orchestrator")
skill_content = await vfs.read(f"{skill_path}/SKILL.md")
```

### Step 3: Add Compatibility Layer

```python
# ~/.agent/compat/symlink_compat.py
"""
Compatibility layer for legacy symlink-based code
"""
from pathlib import Path
from vfs import get_vfs
import asyncio

class SymlinkCompatPath:
    """Drop-in replacement for Path that uses VFS"""
    
    def __init__(self, path: str):
        self.path = path
        self.vfs = get_vfs()
    
    def read_text(self, **kwargs) -> str:
        content_bytes = asyncio.run(self.vfs.read(self._to_virtual(self.path)))
        return content_bytes.decode()
    
    def read_bytes(self) -> bytes:
        return asyncio.run(self.vfs.read(self._to_virtual(self.path)))
    
    def exists(self) -> bool:
        return asyncio.run(self.vfs.exists(self._to_virtual(self.path)))
    
    def _to_virtual(self, path: str) -> str:
        """Convert file system path to virtual path"""
        path_str = str(path)
        
        # Map known symlink paths to virtual paths
        mappings = {
            str(Path.home() / ".agent" / "skills"): "vfs://agent/skills",
            str(Path.home() / ".agent" / "commands"): "vfs://agent/workflows",
            str(Path.home() / ".agent" / "docs"): "vfs://agent/docs",
        }
        
        for fs_path, vfs_path in mappings.items():
            if path_str.startswith(fs_path):
                relative = path_str[len(fs_path):].lstrip('/')
                return f"{vfs_path}/{relative}"
        
        return path_str
    
    def __truediv__(self, other):
        return SymlinkCompatPath(str(Path(self.path) / other))

# Monkey-patch Path (for gradual migration)
# Warning: Use with caution, only during migration
def patch_pathlib():
    import pathlib
    original_path = pathlib.Path
    
    def patched_path(path):
        if ".agent" in str(path):
            return SymlinkCompatPath(path)
        return original_path(path)
    
    pathlib.Path = patched_path
```

### Step 4: Validate Migration

```bash
# Run validation script
python ~/.agent/scripts/validate-vfs-migration.py

# Expected output:
# ✓ VFS configuration loaded
# ✓ All mounts accessible
# ✓ Skills resolvable
# ✓ Workflows resolvable
# ✓ Cache functional
# ✓ Backwards compatibility maintained
```

---

## 📊 Performance Benchmarks

### Target Performance

| Operation | Target | Current (Symlinks) |
|-----------|--------|--------------------|
| Read (cached) | < 1ms | N/A |
| Read (uncached) | < 50ms | ~10ms |
| Write | < 100ms | ~20ms |
| Skill resolution | < 10ms | ~5ms |
| Mount operation | < 5ms | Instant |

### Optimization Strategies

1. **Aggressive Caching**: Cache file contents with TTL
2. **Lazy Loading**: Only load when accessed
3. **Parallel Reads**: Use asyncio for concurrent reads
4. **Index Building**: Pre-build skill/workflow indexes
5. **Compression**: Compress large files in cache

---

## 🔒 Security Considerations

### Access Control

```python
class SecureVFS(UniversalVFS):
    """VFS with access control"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_rules = {}
    
    def set_access_rule(self, virtual_path: str, allowed_providers: List[str]):
        """Set access rules for path"""
        self.access_rules[virtual_path] = allowed_providers
    
    async def read(self, virtual_path: str, provider: str = None, **kwargs):
        """Read with access control"""
        if virtual_path in self.access_rules:
            allowed = self.access_rules[virtual_path]
            if provider not in allowed:
                raise PermissionError(f"Provider {provider} not allowed to access {virtual_path}")
        
        return await super().read(virtual_path, **kwargs)
```

### Integrity Verification

```python
import hashlib

async def verify_integrity(vfs: UniversalVFS, path: str, expected_hash: str):
    """Verify file integrity"""
    content = await vfs.read(path, use_cache=False)
    actual_hash = hashlib.sha256(content).hexdigest()
    
    if actual_hash != expected_hash:
        raise SecurityError(f"Integrity check failed for {path}")
    
    return True
```

---

## 🎯 Success Criteria

### Phase 1 (MVP)
- ✅ VFS can mount local directories
- ✅ Read/write operations work
- ✅ Skill resolution works
- ✅ Backwards compatibility maintained
- ✅ Tests pass

### Phase 2 (Feature Complete)
- ✅ HTTP backend functional
- ✅ Git backend functional
- ✅ Caching optimized
- ✅ All legacy code migrated
- ✅ Symlinks removed

### Phase 3 (Production Ready)
- ✅ Performance targets met
- ✅ Security audit passed
- ✅ Documentation complete
- ✅ Migration guide validated
- ✅ Zero production issues for 2 weeks

---

**Next Steps**: Start with the core VFS implementation and test thoroughly before migrating existing code.
