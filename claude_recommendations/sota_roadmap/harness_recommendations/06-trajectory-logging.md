---
title: "Implement Comprehensive Trajectory Logging"
labels: high-priority, observability, enhancement
priority: P1
---

## Problem Statement

No structured logging of agent execution:
- Can't reproduce bugs from past sessions
- No audit trail of agent actions
- Difficult to understand agent decision-making
- Can't analyze performance over time
- No data for debugging or optimization

## Proposed Solution

Implement comprehensive trajectory logging with replay capability:

```python
class TrajectoryLogger:
    """Log agent execution for debugging and analysis"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.current_trajectory = []
        self.session_id = str(uuid4())
        
    def log_step(self, step_data: dict):
        """Log a single execution step"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'step_number': len(self.current_trajectory) + 1,
            **step_data
        }
        self.current_trajectory.append(entry)
        self._write_to_disk(entry)
        
    def log_tool_call(self, tool: str, input: dict, output: dict, 
                     execution_time: float):
        """Log tool execution"""
        self.log_step({
            'type': 'tool_call',
            'tool': tool,
            'input': input,
            'output': output,
            'execution_time_ms': execution_time * 1000
        })
        
    def get_trajectory(self) -> list:
        """Get full execution trajectory"""
        return self.current_trajectory
        
    def replay(self, trajectory_file: Path):
        """Replay a logged trajectory"""
        # Load trajectory from file
        # Re-execute each step
        # Compare outputs
```

## Log Structure

Each step logged as JSON:

```json
{
  "timestamp": "2026-02-12T10:30:45Z",
  "session_id": "abc123",
  "step_number": 5,
  "type": "tool_call",
  "agent_message": "I'll add error handling to the parser",
  "agent_thinking": "The parser currently crashes on invalid JSON...",
  "tool": "edit_file",
  "input": {
    "path": "src/parser.py",
    "old_str": "def parse(text):\n    return json.loads(text)",
    "new_str": "def parse(text):\n    try:\n        return json.loads(text)\n    except JSONDecodeError as e:\n        logger.error(f'Parse failed: {e}')\n        return None"
  },
  "output": {
    "success": true,
    "lines_changed": 3
  },
  "execution_time_ms": 42,
  "context_size_tokens": 8450,
  "model": "claude-sonnet-4-20250514",
  "success": true
}
```

## Key Features

### 1. Structured JSONL Format
- One JSON object per line
- Easy to parse and analyze
- Streamable for long sessions

### 2. Complete Step Information
- Agent's reasoning (thinking)
- Tool calls with inputs/outputs
- Execution times
- Token usage
- Model used
- Success/failure status

### 3. Replay Capability
```python
# Replay a past session
replayer = TrajectoryReplayer('logs/session_abc123.jsonl')
replayer.replay(
    stop_at_step=10,  # Debug first 10 steps
    interactive=True   # Pause at each step
)
```

### 4. Analysis Tools
```python
# Analyze performance
analyzer = TrajectoryAnalyzer('logs/')
analyzer.average_step_time()  # 2.3s
analyzer.most_used_tools()    # {'edit': 45, 'read': 23, ...}
analyzer.success_rate()       # 0.87
analyzer.token_usage()        # Total: 450k tokens
```

### 5. Comparison
```python
# Compare two approaches
comparer = TrajectoryComparer(
    'logs/session_1.jsonl',
    'logs/session_2.jsonl'
)
comparer.show_differences()
```

## Implementation Details

1. **Create TrajectoryLogger class** (`src/agent_harness/logging.py`)

2. **Integrate with harness**:
   - Log after each agent response
   - Log before/after each tool call
   - Log context management events
   - Log errors and exceptions

3. **Log file organization**:
```
logs/
  2026-02-12/
    session_abc123_1030.jsonl
    session_def456_1245.jsonl
  2026-02-11/
    session_xyz789_0900.jsonl
```

4. **Add log rotation**:
   - Daily directories
   - Optional compression of old logs
   - Configurable retention (default 30 days)

5. **Create analysis tools**:
   - CLI for querying logs
   - Export to CSV/pandas
   - Visualization scripts

6. **Add replay mechanism**:
   - Load trajectory from file
   - Optionally re-execute tools
   - Compare expected vs actual outputs
   - Identify where behavior diverged

## What to Log

### Essential (Always)
- Timestamp
- Session/step ID
- Agent message/reasoning
- Tool calls (input/output)
- Success/failure
- Model used

### Important (Usually)
- Execution time
- Token usage
- Context size
- Permissions granted

### Optional (Debug mode)
- Full message history
- Agent's thinking/reasoning
- Compression events
- Cache hits/misses

### Don't Log
- Secrets/credentials
- Full file contents (just diffs)
- Binary data (just metadata)

## Configuration

```python
logging_config = {
    'enabled': True,
    'log_dir': 'logs/',
    'format': 'jsonl',  # or 'json', 'csv'
    'rotation': 'daily',
    'retention_days': 30,
    'compress_old': True,
    'include_thinking': True,
    'include_full_context': False  # Only in debug mode
}
```

## Acceptance Criteria

- [ ] Each step logged with complete information
- [ ] JSONL format valid and parseable
- [ ] Log files organized by date
- [ ] Replay works from any logged session
- [ ] Analysis tools provide useful metrics
- [ ] Minimal performance overhead (<5%)
- [ ] Log rotation works correctly
- [ ] Old logs compressed/deleted
- [ ] Sensitive data excluded from logs
- [ ] Documentation includes examples
- [ ] CLI tools for log analysis
- [ ] Tests cover logging and replay

## Dependencies

- None (independent feature)

## Estimated Effort

Medium (1 week)

## Example Analysis

```bash
# Find all failed sessions
python -m agent_harness.logs analyze --status=failed

# Show average step time by tool
python -m agent_harness.logs stats --group-by=tool

# Compare two sessions
python -m agent_harness.logs compare session_1.jsonl session_2.jsonl

# Replay a session
python -m agent_harness.logs replay session_abc123.jsonl --interactive

# Export to CSV for analysis
python -m agent_harness.logs export --format=csv --output=data.csv
```

## Future Enhancements

- Real-time log streaming
- Web UI for log visualization
- Integration with observability tools (Datadog, etc.)
- Anomaly detection
- Cost analysis per session
- A/B test comparison
