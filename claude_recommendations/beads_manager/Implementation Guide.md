# Beads Manager Implementation Guide

This guide walks you through implementing the beads-manager skill in your agent-harness environment.

## Prerequisites

Before starting, ensure you have:

- [ ] Python 3.8 or later installed
- [ ] Beads CLI installed and working (`bd --version`)
- [ ] At least two repositories using beads issue tracking
- [ ] Git installed
- [ ] Write access to the repositories

## Installation Steps

### Step 1: Copy Skill to Skills Directory

```bash
# Create skills directory if it doesn't exist
mkdir -p ~/.gemini/antigravity/skills/

# Copy beads-manager skill
cp -r beads-manager ~/.gemini/antigravity/skills/

# Verify structure
ls -la ~/.gemini/antigravity/skills/beads-manager/
```

Expected output:
```
drwxr-xr-x  SKILL.md
drwxr-xr-x  README.md
drwxr-xr-x  scripts/
drwxr-xr-x  tests/
drwxr-xr-x  config/
drwxr-xr-x  requirements.txt
```

### Step 2: Install Dependencies

```bash
cd ~/.gemini/antigravity/skills/beads-manager

# Install Python dependencies
pip install -r requirements.txt --break-system-packages

# Verify installation
python -c "import yaml; print('YAML installed:', yaml.__version__)"
```

### Step 3: Configure Repositories

```bash
# Copy template configurations
cp config/repos.yaml.template config/repos.yaml
cp config/defaults.yaml.template config/defaults.yaml

# Edit repos.yaml with your repository paths
vim config/repos.yaml
```

**Update `config/repos.yaml`:**

```yaml
repositories:
  agent-harness:
    path: /path/to/your/agent-harness  # ← UPDATE THIS
    beads_dir: .beads
    enabled: true
    default_assignee: "@agent"
  
  lightrag:
    path: /path/to/your/LightRAG  # ← UPDATE THIS
    beads_dir: .beads
    enabled: true
    default_assignee: "@agent"
  
  # Add more repositories as needed

sync_settings:
  auto_sync: true
  sync_on_status_change: true

search_settings:
  default_repos: all
  max_results: 100
```

**Verify paths are correct:**

```bash
# Test each repository path
ls /path/to/your/agent-harness/.beads
ls /path/to/your/LightRAG/.beads

# Both should show: issues/  config/  (or similar beads structure)
```

### Step 4: Test Basic Functionality

```bash
cd ~/.gemini/antigravity/skills/beads-manager

# Test listing (should show all issues from all repos)
python scripts/beads_manager.py list --all

# Test showing help
python scripts/beads_manager.py --help

# Test create (dry-run mode if available, or create a test issue)
python scripts/beads_manager.py create \
  --repo agent-harness \
  --title "Test issue from beads-manager" \
  --type task \
  --priority 2
```

### Step 5: Run Tests

```bash
# Run unit tests
pytest tests/test_beads_manager.py -v

# Run integration tests (requires beads CLI)
pytest tests/test_integration.py -v

# Run all tests with coverage
pytest tests/ --cov=scripts --cov-report=term-missing
```

Expected output:
```
tests/test_beads_manager.py::TestBeadsManagerInit::test_init_loads_repos PASSED
tests/test_beads_manager.py::TestCreateIssue::test_create_issue_basic PASSED
...
=================== X passed in Y.YYs ===================
```

### Step 6: Create Shell Aliases (Optional)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Beads Manager Aliases
export BEADS_MANAGER_PATH="$HOME/.gemini/antigravity/skills/beads-manager"

# Create issue alias
alias bd-create='python $BEADS_MANAGER_PATH/scripts/beads_manager.py create'

# List issues alias
alias bd-list='python $BEADS_MANAGER_PATH/scripts/beads_manager.py list'

# Show issue alias  
alias bd-show='python $BEADS_MANAGER_PATH/scripts/beads_manager.py show'

# Create linked issues alias
alias bd-create-linked='python $BEADS_MANAGER_PATH/scripts/beads_manager.py create-linked'
```

Reload shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Test aliases:
```bash
bd-list --all
```

### Step 7: Agent Integration

Update your agent's system prompt or skill registry to include beads-manager:

**Option A: Add to agent skills list**

```python
# In your agent configuration
AVAILABLE_SKILLS = [
    "git",
    "debugging",
    "code-review",
    "beads-manager",  # ← Add this
    # ... other skills
]
```

**Option B: Add to orchestrator configuration**

```yaml
# In Orchestrator/config/skills.yaml
skills:
  beads-manager:
    path: ~/.gemini/antigravity/skills/beads-manager/SKILL.md
    enabled: true
    priority: medium
    triggers:
      - "cross-repo"
      - "multi-repo"
      - "beads issue"
      - "issue management"
```

## Verification Checklist

After installation, verify each item:

- [ ] Skill directory exists at `~/.gemini/antigravity/skills/beads-manager/`
- [ ] Dependencies installed: `python -c "import yaml"`
- [ ] Configuration files created and edited:
  - [ ] `config/repos.yaml` with correct paths
  - [ ] `config/defaults.yaml` customized
- [ ] Repository paths are valid: `ls /path/to/repo/.beads`
- [ ] Basic commands work:
  - [ ] `python scripts/beads_manager.py list --all`
  - [ ] `python scripts/beads_manager.py --help`
- [ ] Tests pass: `pytest tests/test_beads_manager.py`
- [ ] Aliases created (optional): `bd-list --all`
- [ ] Agent can invoke skill: Agent sees beads-manager in skill list

## Usage Examples

### Example 1: Create Issue in Specific Repo

```bash
# Create feature request in agent-harness
python scripts/beads_manager.py create \
  --repo agent-harness \
  --title "Add performance monitoring" \
  --type feature \
  --priority 2 \
  --description "Track agent performance metrics"
```

### Example 2: Search for High-Priority Issues

```bash
# Find all P0 and P1 issues across all repos
python scripts/beads_manager.py list \
  --all \
  --priority "0,1" \
  --status open
```

### Example 3: Create Linked Issues

```bash
# Create feature that depends on work in another repo
python scripts/beads_manager.py create-linked \
  --primary agent-harness:"Expose debug API" \
  --depends lightrag:"Add debug info method" \
  --priority 2
```

### Example 4: Show Issue Details

```bash
# Auto-detect which repo contains the issue
python scripts/beads_manager.py show bd-abc123

# Or specify repo explicitly
python scripts/beads_manager.py show bd-abc123 --repo agent-harness
```

## Troubleshooting

### Issue: "Repository registry not found"

**Symptom:**
```
FileNotFoundError: Repository registry not found: /path/to/config/repos.yaml
Run: beads-manager --init
```

**Solution:**
```bash
# Create config from template
cd ~/.gemini/antigravity/skills/beads-manager
cp config/repos.yaml.template config/repos.yaml

# Edit with your paths
vim config/repos.yaml
```

### Issue: "Unknown repository: repo-name"

**Symptom:**
```
ValueError: Unknown repository: my-repo
```

**Solution:**
```bash
# Check repos.yaml
cat config/repos.yaml

# Add missing repository:
vim config/repos.yaml
# Add:
# my-repo:
#   path: /path/to/my-repo
#   beads_dir: .beads
#   enabled: true
```

### Issue: "Beads CLI not found"

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'bd'
```

**Solution:**
```bash
# Install beads CLI
pip install beads-cli --break-system-packages

# Or add to PATH
export PATH="$PATH:/path/to/beads/bin"

# Verify
which bd
bd --version
```

### Issue: Tests failing with "Permission denied"

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: '/tmp/test-repo/.beads'
```

**Solution:**
```bash
# Fix permissions on test directories
chmod -R u+w ~/.gemini/antigravity/skills/beads-manager/tests/

# Or run tests with specific temp directory
pytest tests/ --basetemp=/tmp/beads-manager-tests
```

### Issue: Import errors in tests

**Symptom:**
```
ModuleNotFoundError: No module named 'scripts.beads_manager'
```

**Solution:**
```bash
# Install package in development mode
cd ~/.gemini/antigravity/skills/beads-manager
pip install -e . --break-system-packages

# Or run tests from package root
cd ~/.gemini/antigravity/skills/beads-manager
pytest tests/
```

## Advanced Configuration

### Custom Templates

Edit `config/repos.yaml` to add custom issue templates:

```yaml
templates:
  security-fix:
    type: bug
    priority: 0
    labels:
      - security
      - critical
    description_template: |
      ## Security Issue
      
      **Severity:** [Critical/High/Medium/Low]
      **Attack Vector:** 
      **Impact:**
      **Mitigation:**
      
      ## Affected Versions
      
      ## Fix Description
```

Usage:
```bash
python scripts/beads_manager.py create \
  --template security-fix \
  --repo agent-harness \
  --title "XSS vulnerability in input validation"
```

### Auto-Sync Configuration

Enable automatic synchronization of linked issues:

```yaml
# In repos.yaml
sync_settings:
  auto_sync: true
  sync_on_status_change: true
  bidirectional: true
  sync_labels: true
  add_sync_comments: true
```

### Performance Tuning

For large numbers of issues:

```yaml
# In defaults.yaml
performance:
  enable_cache: true
  cache_ttl: 600  # 10 minutes
  max_cache_size: 100  # MB
  parallel: true
  max_workers: 8  # Increase for faster multi-repo operations
```

## Maintenance

### Updating Configuration

```bash
# Edit configuration
vim ~/.gemini/antigravity/skills/beads-manager/config/repos.yaml

# No restart needed - changes take effect immediately
```

### Adding New Repositories

```bash
# Edit repos.yaml
vim config/repos.yaml

# Add new repository:
# new-repo:
#   path: /path/to/new-repo
#   beads_dir: .beads
#   enabled: true

# Test immediately
python scripts/beads_manager.py list --repo new-repo
```

### Upgrading

```bash
# Backup current config
cp config/repos.yaml config/repos.yaml.backup

# Update skill files
cp -r /path/to/new/beads-manager/* ~/.gemini/antigravity/skills/beads-manager/

# Restore config
cp config/repos.yaml.backup config/repos.yaml

# Update dependencies
pip install -r requirements.txt --upgrade --break-system-packages

# Run tests
pytest tests/
```

## Integration with Other Skills

### With Git Skill

```bash
# Create issue, then immediately create feature branch
issue_id=$(python scripts/beads_manager.py create \
  --repo agent-harness \
  --title "Add feature X" \
  --type feature | grep -oP 'bd-[a-z0-9]+')

cd /path/to/agent-harness
git checkout -b "feature/${issue_id}"
```

### With Orchestrator

```yaml
# In Orchestrator workflow
initialization:
  - check: beads issue assigned
    command: python scripts/beads_manager.py show $ISSUE_ID
  - check: dependencies resolved
    command: python scripts/beads_manager.py show $ISSUE_ID | grep -q "depends_on: \[\]"
```

### With Code Review

```bash
# Create code review issue linked to implementation
impl_issue="bd-abc123"

python scripts/beads_manager.py create \
  --repo agent-harness \
  --title "Code review for $impl_issue" \
  --type task \
  --depends-on "$impl_issue"
```

## Support and Feedback

- **Documentation:** See `SKILL.md` for complete skill documentation
- **Examples:** Check `README.md` for usage examples
- **Issues:** Report bugs in the agent-harness repository
- **Contributing:** Follow patterns from `skill-making/SKILL.md`

## Next Steps

After successful installation:

1. **Read SKILL.md** - Understand all features
2. **Try examples** - Practice with test repos
3. **Customize config** - Tailor to your workflow
4. **Train agents** - Ensure agents know about the skill
5. **Monitor usage** - Track how skill is being used
6. **Provide feedback** - Help improve the skill

---

**Version:** 1.0.0  
**Last Updated:** 2026-02-17  
**Status:** Production Ready
