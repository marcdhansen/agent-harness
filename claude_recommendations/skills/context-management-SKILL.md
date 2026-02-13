---
name: context-management
description: Manage agent context window effectively for long sessions, including compression, summarization, and working memory optimization.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# 🧠 Context Management Skill

**Purpose**: Optimize agent context window usage for long coding sessions, preventing context overflow and maintaining relevant information.

## 🎯 Mission

- Monitor context window usage
- Compress or summarize old information
- Maintain working memory efficiently
- Prevent context overflow
- Preserve critical information

## 📋 When to Use This Skill

Use this skill when:
- Context window reaching 80%+ capacity
- Long debugging or exploration sessions
- Complex refactoring with many files
- Multi-day work on same feature
- Agent seems to "forget" earlier context

## 📊 Context Window Monitoring

### Check Current Usage

```bash
#!/bin/bash
# scripts/check_context_usage.sh

# Estimate current context size
# Note: Actual calculation depends on model tokenizer

estimate_tokens() {
    local file=$1
    # Rough estimate: 1 token ≈ 4 characters
    local chars=$(wc -m < "$file")
    echo $((chars / 4))
}

# Count conversation history tokens
CONVERSATION_TOKENS=0
if [ -f ".agent/conversation_history.txt" ]; then
    CONVERSATION_TOKENS=$(estimate_tokens ".agent/conversation_history.txt")
fi

# Count code context tokens
CODE_TOKENS=0
for file in $(git diff --name-only HEAD~1); do
    if [ -f "$file" ]; then
        FILE_TOKENS=$(estimate_tokens "$file")
        CODE_TOKENS=$((CODE_TOKENS + FILE_TOKENS))
    fi
done

# Count working memory tokens
MEMORY_TOKENS=0
if [ -f "WorkingMemory.md" ]; then
    MEMORY_TOKENS=$(estimate_tokens "WorkingMemory.md")
fi

TOTAL_TOKENS=$((CONVERSATION_TOKENS + CODE_TOKENS + MEMORY_TOKENS))

# Assume model has 200k token context (adjust per model)
MODEL_CONTEXT=200000
USAGE_PERCENT=$((TOTAL_TOKENS * 100 / MODEL_CONTEXT))

echo "Context Usage Report"
echo "===================="
echo "Conversation: ${CONVERSATION_TOKENS} tokens"
echo "Code files: ${CODE_TOKENS} tokens"
echo "Working memory: ${MEMORY_TOKENS} tokens"
echo "Total: ${TOTAL_TOKENS} tokens"
echo "Model capacity: ${MODEL_CONTEXT} tokens"
echo "Usage: ${USAGE_PERCENT}%"

if [ $USAGE_PERCENT -gt 80 ]; then
    echo ""
    echo "⚠️ WARNING: Context usage >80%"
    echo "Consider compression or summarization"
    exit 1
elif [ $USAGE_PERCENT -gt 60 ]; then
    echo ""
    echo "⚠️ NOTICE: Context usage >60%"
    echo "Monitor closely"
fi
```

### Automatic Monitoring

```bash
# Add to .bashrc or agent startup script
check_context_on_command() {
    # Check context before major operations
    local usage=$(bash scripts/check_context_usage.sh | grep "Usage:" | grep -oE '[0-9]+')
    
    if [ $usage -gt 85 ]; then
        echo "⚠️ Context at ${usage}% - Compression recommended"
        read -p "Compress context now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            /context-management --compress
        fi
    fi
}

# Hook into git operations
alias git='check_context_on_command; command git'
```

## 🗜️ Context Compression Strategies

### Strategy 1: Summarize Old Conversations

```bash
#!/bin/bash
# scripts/compress_conversation.sh

# Summarize conversation history older than 1 hour

CUTOFF_TIME=$(($(date +%s) - 3600))  # 1 hour ago

# Split conversation into old and recent
awk -v cutoff="$CUTOFF_TIME" '
/^## Message/ {
    timestamp = $NF
    if (timestamp < cutoff) {
        old = old $0 "\n"
    } else {
        recent = recent $0 "\n"
    }
    next
}
{ 
    if (timestamp < cutoff) {
        old = old $0 "\n"
    } else {
        recent = recent $0 "\n"
    }
}
END {
    print "OLD:" old
    print "RECENT:" recent
}
' .agent/conversation_history.txt > /tmp/split_conversation.txt

# Summarize old conversation
OLD_CONVERSATION=$(grep -A 9999 "OLD:" /tmp/split_conversation.txt | tail -n +2)

# Generate summary (this would call AI model in real implementation)
cat > .agent/conversation_summary.txt << EOF
# Conversation Summary (up to $(date -r $CUTOFF_TIME))

## Key Decisions Made
- Decided to use JWT for authentication
- Chose PostgreSQL over MongoDB for user data
- Agreed on REST API design

## Problems Solved
- Fixed memory leak in parser (issue #123)
- Resolved import circular dependency
- Optimized database queries (50ms → 10ms)

## Current State
- Authentication implemented and tested
- Database schema finalized
- API endpoints 80% complete
EOF

# Replace old conversation with summary
RECENT_CONVERSATION=$(grep -A 9999 "RECENT:" /tmp/split_conversation.txt | tail -n +2)
cat .agent/conversation_summary.txt > .agent/conversation_history.txt
echo "$RECENT_CONVERSATION" >> .agent/conversation_history.txt

echo "✅ Conversation compressed"
echo "Saved ~$(($(echo "$OLD_CONVERSATION" | wc -m) / 4)) tokens"
```

### Strategy 2: Deduplicate Code Context

```bash
#!/bin/bash
# scripts/deduplicate_context.sh

# Remove duplicate file references

CONTEXT_FILE="WorkingMemory.md"

# Find files referenced multiple times
FILES_SEEN=()
DEDUPLICATED=""

while IFS= read -r line; do
    if [[ $line =~ ^File:\ (.+) ]]; then
        FILE="${BASH_REMATCH[1]}"
        
        if [[ " ${FILES_SEEN[@]} " =~ " ${FILE} " ]]; then
            # Skip duplicate, keep only reference
            DEDUPLICATED+="File: $FILE (see above for content)\n"
            # Skip next N lines (file content)
            for i in {1..20}; do
                read -r line || break
            done
        else
            # First occurrence, keep full content
            FILES_SEEN+=("$FILE")
            DEDUPLICATED+="$line\n"
        fi
    else
        DEDUPLICATED+="$line\n"
    fi
done < "$CONTEXT_FILE"

echo -e "$DEDUPLICATED" > "$CONTEXT_FILE"
echo "✅ Deduplicated file references"
```

### Strategy 3: Evict Stale Information

```bash
#!/bin/bash
# scripts/evict_stale.sh

# Remove context for files that are no longer being modified

WORKING_MEMORY="WorkingMemory.md"
STALE_THRESHOLD=7200  # 2 hours in seconds

# Get list of recently modified files
RECENT_FILES=$(find . -type f -mmin -120 -name "*.py")

# Extract files from working memory
awk '/^File: / {print $2}' "$WORKING_MEMORY" | while read -r file; do
    if [ ! -f "$file" ]; then
        # File deleted, remove from working memory
        echo "Removing deleted file: $file"
        sed -i "/^File: $file/,/^File: /d" "$WORKING_MEMORY"
    elif ! echo "$RECENT_FILES" | grep -q "$file"; then
        # File not recently modified, evict
        echo "Evicting stale file: $file (not modified in 2h)"
        sed -i "/^File: $file/,/^File: /d" "$WORKING_MEMORY"
    fi
done

echo "✅ Evicted stale information"
```

## 💾 Working Memory Optimization

### Maintain Focused Working Memory

```markdown
# WorkingMemory.md (Optimized Structure)

## Current Task
**Issue**: TASK-123 - Add user authentication
**Status**: Implementation 60% complete
**Next Steps**: 
1. Implement token refresh logic
2. Add logout endpoint
3. Write integration tests

## Active Files
### src/auth.py (Modified 5 min ago)
- `authenticate_user()` - Main auth function
- `generate_token()` - JWT token generation
- **Current issue**: Need to add token refresh

### src/models.py (Modified 10 min ago)
- `User` model - Updated with last_login field
- Migration created: 0042_add_last_login.py

## Key Context
- Using JWT (not sessions) - decided 2h ago
- Token expiry: 1 hour (configurable)
- Refresh tokens valid for 30 days
- Database: PostgreSQL users table

## Recent Decisions
- [1h ago] Use bcrypt for password hashing (not sha256)
- [2h ago] Store tokens in httpOnly cookies (not localStorage)
- [3h ago] Implement rate limiting on auth endpoints

## To Remember
- Security test suite due before merge
- Performance target: <100ms auth check
- Must work with existing session middleware

---

## Archived Context
[Moved to .agent/archive/TASK-123-context.md]
- Initial planning notes
- Alternative approaches considered
- Completed sub-tasks
```

### Archival System

```bash
#!/bin/bash
# scripts/archive_context.sh

# Archive completed or stale context

TASK_ID="TASK-123"
ARCHIVE_DIR=".agent/archive"

mkdir -p "$ARCHIVE_DIR"

# Extract completed sections from WorkingMemory
grep -A 999 "## Archived Context" WorkingMemory.md > "$ARCHIVE_DIR/${TASK_ID}-context.md"

# Remove archived sections from working memory
sed -i '/## Archived Context/,$d' WorkingMemory.md

# Add archive reference
echo "" >> WorkingMemory.md
echo "## Archived Context" >> WorkingMemory.md
echo "[Moved to $ARCHIVE_DIR/${TASK_ID}-context.md]" >> WorkingMemory.md

echo "✅ Context archived to $ARCHIVE_DIR/${TASK_ID}-context.md"
```

## 🎯 Smart Context Loading

### Load Only Relevant Context

```bash
#!/bin/bash
# scripts/load_relevant_context.sh

# Load only context relevant to current task

CURRENT_TASK="Add authentication"

# Load files matching current task keywords
KEYWORDS="auth login user session token"

echo "# Relevant Context for: $CURRENT_TASK"
echo ""

# Load relevant files
for keyword in $KEYWORDS; do
    # Find files containing keyword
    FILES=$(rg -l "$keyword" src/ --type py)
    
    for file in $FILES; do
        echo "## File: $file"
        # Show only relevant sections (not entire file)
        rg "$keyword" "$file" -B 2 -A 5 || true
        echo ""
    done
done

# Load relevant past decisions
echo "## Relevant Decisions"
grep -i "$KEYWORDS" .agent/decisions.log | tail -5

# Load relevant issues
echo "## Related Issues"
bd list --labels auth --status closed | head -3
```

## 🔄 Context Restoration

### Restore Context After Break

```bash
#!/bin/bash
# scripts/restore_context.sh

# Restore context after long break (e.g., next day)

TASK_ID=$(cat .beads/current)

echo "Restoring context for $TASK_ID..."
echo ""

# 1. Show task summary
echo "## Task Summary"
bd show "$TASK_ID" --format markdown

# 2. Show recent activity
echo ""
echo "## Recent Activity (last 24h)"
git log --since="24 hours ago" --oneline --author="$(git config user.name)"

# 3. Show working memory
echo ""
echo "## Working Memory"
cat WorkingMemory.md

# 4. Show recent decisions
echo ""
echo "## Recent Decisions"
tail -10 .agent/decisions.log

# 5. Show current state
echo ""
echo "## Current State"
git status
echo ""
echo "Modified files:"
git diff --name-only

# 6. Recommend next action
echo ""
echo "## Recommended Next Action"
echo "Based on WorkingMemory.md, next steps:"
grep "Next Steps:" -A 3 WorkingMemory.md
```

## ⚙️ Configuration

```yaml
# config/context_management.yaml

monitoring:
  check_frequency: "every_major_operation"  # or "every_15_min"
  warning_threshold: 60  # percent
  critical_threshold: 85  # percent

compression:
  auto_compress: true
  compress_threshold: 80  # percent
  conversation_age_threshold: 3600  # seconds (1 hour)
  
  strategies:
    - summarize_old_conversations
    - deduplicate_code_context
    - evict_stale_information

working_memory:
  max_active_files: 10
  max_file_context_lines: 50  # per file
  archive_completed_sections: true
  
eviction:
  stale_file_threshold: 7200  # seconds (2 hours)
  stale_conversation_threshold: 3600  # seconds (1 hour)

restoration:
  auto_restore_on_start: true
  restore_command: "scripts/restore_context.sh"
```

## 📊 Context Metrics

```bash
#!/bin/bash
# scripts/context_metrics.sh

# Generate context usage report

cat > .agent/context_report.md << EOF
# Context Management Report

## Current Usage
- Total tokens: $(estimate_total_tokens)
- Usage: $(get_usage_percent)%
- Status: $(get_status)

## Breakdown
- Conversation: $(estimate_conversation_tokens) tokens
- Code files: $(estimate_code_tokens) tokens  
- Working memory: $(estimate_memory_tokens) tokens
- Archived: $(estimate_archived_tokens) tokens

## Compressions (Last 7 Days)
- Total compressions: $(count_compressions)
- Tokens saved: $(calculate_tokens_saved)
- Avg compression ratio: $(calculate_compression_ratio)

## Evictions (Last 7 Days)
- Files evicted: $(count_evictions)
- Conversation summaries: $(count_summaries)

## Recommendations
- $(generate_recommendations)
EOF

cat .agent/context_report.md
```

## ✅ Best Practices

### For Long Sessions

1. **Regular monitoring** - Check context every hour
2. **Proactive compression** - Don't wait for 90%+ usage
3. **Focused working memory** - Only keep active task context
4. **Archive completed work** - Move finished context to archive
5. **Restore strategically** - Load only relevant context on return

### For Complex Refactoring

1. **Chunk the work** - Break into smaller tasks with separate contexts
2. **Document key decisions** - Don't rely on conversation history
3. **Use working memory wisely** - Summarize file contents, don't copy entire files
4. **Compress frequently** - High turnover of context in refactoring

### For Multi-Day Tasks

1. **Daily context restoration** - Start each day with context restore
2. **End-of-day archival** - Archive completed sections before stopping
3. **Decision log** - Keep explicit log of architectural decisions
4. **Working memory snapshot** - Save state at end of each day

## 🔗 Integration Points

- **Orchestrator**: Check context before initialization
- **Finalization**: Archive context during finalization
- **Planning**: Load relevant context during planning
- **Reflection**: Include context management efficiency in reflection

---

**Remember**: Context management is about keeping the right information available, not keeping all information available. Be strategic about what to preserve.
