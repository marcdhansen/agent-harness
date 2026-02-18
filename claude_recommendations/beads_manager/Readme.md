# Beads Manager - Cross-Repository Issue Management

Manage beads issues across multiple repositories from a single context without switching terminals or losing workflow state.

## Quick Start

### Installation

```bash
# 1. Install dependencies
pip install pyyaml --break-system-packages

# 2. Create config directory
mkdir -p ~/.gemini/antigravity/skills/beads-manager/config

# 3. Copy skill to skills directory
cp -r beads-manager ~/.gemini/antigravity/skills/

# 4. Initialize configuration
cd ~/.gemini/antigravity/skills/beads-manager
cp config/repos.yaml.template config/repos.yaml
cp config/defaults.yaml.template config/defaults.yaml

# 5. Edit config/repos.yaml with your repository paths
vim config/repos.yaml
```

### Basic Usage

```bash
# Create issue in specific repo
python scripts/beads_manager.py create \
  --repo agent-harness \
  --title "Add debugging skill" \
  --type task \
  --priority 2

# List all open issues
python scripts/beads_manager.py list --all

# Show issue details
python scripts/beads_manager.py show bd-abc123

# Create linked issues across repos
python scripts/beads_manager.py create-linked \
  --primary agent-harness:"Add API endpoint" \
  --depends lightrag:"Expose data method" \
  --priority 2
```

## Features

- ✅ **Cross-repo issue creation** - Create issues in any tracked repo
- ✅ **Unified search** - Search issues across all repositories
- ✅ **Linked issues** - Create and manage dependencies between repos
- ✅ **Batch operations** - Update multiple issues at once
- ✅ **Auto-detection** - Automatically find which repo contains an issue
- ✅ **Non-interactive mode** - CI/CD compatible
- ✅ **Fallback support** - Graceful degradation to manual beads CLI

## Architecture

```
beads-manager/
├── SKILL.md              # Complete skill documentation
├── README.md             # This file
├── scripts/
│   ├── beads_manager.py  # Main orchestrator
│   ├── repo_registry.py  # Repository configuration (future)
│   └── issue_sync.py     # Sync logic (future)
├── tests/
│   ├── test_beads_manager.py
│   └── test_integration.py
└── config/
    ├── repos.yaml.template
    └── defaults.yaml.template
```

## Configuration

### Repository Registry (`config/repos.yaml`)

```yaml
repositories:
  agent-harness:
    path: /path/to/agent-harness
    beads_dir: .beads
    enabled: true
    default_assignee: "@agent"
  
  lightrag:
    path: /path/to/LightRAG
    beads_dir: .beads
    enabled: true

sync_settings:
  auto_sync: true
  sync_on_status_change: true

search_settings:
  default_repos: all
  max_results: 100
```

### Defaults (`config/defaults.yaml`)

```yaml
defaults:
  type: task
  priority: 2
  status: open
  assignee: "@current-agent"

display:
  format: table
  color: true

behavior:
  confirm_bulk: true
  cache_duration: 300
```

## Examples

### Example 1: Feature Spanning Multiple Repos

```bash
# Create issues with dependencies
python scripts/beads_manager.py create-linked \
  --primary agent-harness:"Add /debug endpoint" \
  --depends lightrag:"Expose debug info" \
  --priority 2
```

### Example 2: Bug Triage

```bash
# Find all high-priority bugs
python scripts/beads_manager.py list \
  --all \
  --type bug \
  --priority "0,1" \
  --status open
```

### Example 3: Status Dashboard

```bash
# Export all issues for processing
python scripts/beads_manager.py list \
  --all \
  --format json > /tmp/issues.json

# Process with jq
jq '.[] | select(.priority <= 1)' /tmp/issues.json
```

## Testing

```bash
# Run unit tests
pytest tests/test_beads_manager.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run all tests with coverage
pytest tests/ --cov=scripts --cov-report=term-missing
```

## Troubleshooting

### Repository not found

```bash
# Check config
cat config/repos.yaml

# Verify path exists
ls /path/to/repo/.beads
```

### Beads CLI not available

```bash
# Install beads
pip install beads-cli --break-system-packages

# Or add to PATH
export PATH="$PATH:/path/to/beads"
```

### Permission denied

```bash
# Check repo permissions
ls -la /path/to/repo

# Ensure beads is writable
chmod u+w /path/to/repo/.beads
```

## Contributing

1. Follow skill-making patterns from `skill-making/SKILL.md`
2. Include tests for new features
3. Update documentation
4. Maintain backward compatibility with beads CLI

## License

Same as agent-harness project

## Support

- Documentation: See `SKILL.md`
- Issues: Create in agent-harness repo
- Questions: Tag with `beads-manager` label
