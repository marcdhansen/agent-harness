---
title: "Implement Smart Context Window Management"
labels: high-priority, performance, enhancement
priority: P1
---

## Problem Statement

Long coding sessions quickly fill the context window:
- Large tool outputs consume tokens rapidly
- Repeated file reads waste context
- No strategy for what to evict when context is full
- No compression or summarization
- Risk of hitting context limits mid-task
- Expensive to send full context on every request

## Proposed Solution

Implement intelligent context management with compression and eviction:

```python
class ContextManager:
    """Manage context window with smart compression and eviction"""
    
    def __init__(self, max_tokens: int = 180_000):  # Claude Sonnet 4
        self.max_tokens = max_tokens
        self.eviction_threshold = int(max_tokens * 0.85)
        self.cache = {}
        
    def manage_context(self, messages: list) -> list:
        """Compress/evict messages if needed"""
        current_tokens = self.estimate_tokens(messages)
        
        if current_tokens > self.eviction_threshold:
            return self.compress_messages(messages)
        return messages
        
    def compress_messages(self, messages: list) -> list:
        """Apply compression strategy"""
        # Strategy for coding tasks:
        # 1. Keep system prompt (always)
        # 2. Keep recent 5 messages (current context)
        # 3. Summarize middle section
        # 4. Evict large tool outputs to files
        
        compressed = []
        
        # Keep system prompt
        compressed.append(messages[0])
        
        # Summarize middle section
        middle = messages[1:-5]
        summary = self._summarize_section(middle)
        compressed.append({
            'role': 'user',
            'content': f'[Earlier conversation summary: {summary}]'
        })
        
        # Keep recent context
        compressed.extend(messages[-5:])
        
        return compressed
        
    def evict_large_outputs(self, messages: list) -> list:
        """Move large tool outputs to files"""
        for msg in messages:
            if self._is_tool_output(msg) and len(msg['content']) > 5000:
                # Write to cache file
                cache_id = self._save_to_cache(msg['content'])
                msg['content'] = f"[Large output cached: .cache/{cache_id}.txt]"
        return messages
```

## Key Features

### 1. Automatic Compression at Threshold
- Monitor token usage continuously
- Trigger compression at 85% of max
- Multiple compression strategies

### 2. Smart Eviction Strategy
For coding tasks, prioritize:
- **Keep**: System prompt, recent messages (last 5), current file being edited
- **Summarize**: Middle conversation (compress to key points)
- **Evict to disk**: Large tool outputs, old file reads
- **Drop**: Redundant information, duplicate file reads

### 3. Tool Output Caching
```python
# Large outputs saved to disk
{
    'role': 'tool',
    'content': '[Output cached: .cache/output_42.txt]',
    'cache_ref': 'output_42.txt'
}

# If agent needs it later, read from cache
```

### 4. Provider-Specific Optimizations
```python
class AnthropicContextManager(ContextManager):
    """Anthropic-specific optimizations"""
    
    def use_prompt_caching(self, messages: list):
        # Mark system prompt and common prefixes for caching
        # Significantly reduces costs for repeated context
        messages[0]['cache_control'] = {'type': 'ephemeral'}
```

### 5. Deduplication
```python
def deduplicate_file_reads(self, messages: list):
    """Remove duplicate file reads"""
    seen_files = set()
    for msg in messages:
        if self._is_read_tool(msg):
            file_path = self._extract_file_path(msg)
            if file_path in seen_files:
                # Replace with reference
                msg['content'] = f'[Previously read: {file_path}]'
            else:
                seen_files.add(file_path)
```

## Implementation Details

1. **Create ContextManager class** (`src/agent_harness/context.py`)

2. **Add token estimation**:
   - Use tiktoken for accurate counting
   - Support multiple model tokenizers
   - Cache token counts

3. **Implement compression strategies**:
   - Sliding window (keep recent N messages)
   - Summarization (use LLM to compress middle)
   - Eviction (move to files)
   - Deduplication (remove redundant reads)

4. **Add cache system**:
   - Directory: `.cache/` in workspace
   - File naming: `output_{hash}.txt`
   - Cleanup on session end (optional)

5. **Integrate with providers**:
   - Anthropic: Use prompt caching
   - OpenAI: Standard context management
   - Google: Consider context window size

6. **Add configuration**:
```python
context_config = {
    'max_tokens': 180_000,
    'eviction_threshold': 0.85,
    'strategy': 'smart',  # or 'simple', 'aggressive'
    'enable_caching': True,
    'cache_large_outputs': True,
    'cache_threshold': 5000  # tokens
}
```

7. **Monitoring and metrics**:
   - Track token usage over time
   - Log compression events
   - Report savings from caching

## Compression Strategies

### Simple Strategy
- Keep first and last N messages
- Drop everything in middle

### Smart Strategy (Recommended)
1. Always keep: system prompt, last 5 messages
2. Summarize: middle conversation to key points
3. Cache: large tool outputs (>5k tokens)
4. Deduplicate: repeated file reads
5. Drop: redundant tool results

### Aggressive Strategy
- Compress more aggressively
- Smaller context window
- More caching
- Use when approaching limits

## Acceptance Criteria

- [ ] Token counting accurate for all providers
- [ ] Automatic compression at 85% threshold
- [ ] Smart strategy keeps relevant context
- [ ] Large outputs cached to disk successfully
- [ ] Prompt caching works for Anthropic
- [ ] Deduplication removes redundant reads
- [ ] Configuration options work
- [ ] Metrics track token usage and savings
- [ ] No loss of critical information
- [ ] Agent can still complete tasks with compressed context
- [ ] Tests cover all compression strategies
- [ ] Documentation explains compression behavior

## Dependencies

- Issue #1 (Multi-Provider) - provider-specific optimizations

## Estimated Effort

Medium (1 week)

## Examples

```python
# Before compression (150k tokens)
messages = [
    system_prompt,  # 2k tokens
    user_message_1,
    assistant_message_1,
    tool_output_1,  # 50k tokens (large file read)
    user_message_2,
    assistant_message_2,
    tool_output_2,  # 40k tokens (test results)
    # ... more messages
    user_message_recent,
    assistant_message_recent
]

# After compression (80k tokens)
messages = [
    system_prompt,  # 2k (kept, cached)
    {'role': 'user', 'content': '[Earlier: Read large file, ran tests, made edits to parser.py]'},  # 200 tokens (summary)
    {'role': 'tool', 'content': '[Large output cached: .cache/output_1.txt]'},  # 50 tokens (cached)
    {'role': 'tool', 'content': '[Large output cached: .cache/output_2.txt]'},  # 50 tokens (cached)
    user_message_recent,  # kept
    assistant_message_recent  # kept
]
```

## Future Enhancements

- ML-based importance scoring
- Semantic compression (keep semantically unique info)
- User-configurable importance weights
- Context reconstruction from cache
- Multi-turn context optimization
