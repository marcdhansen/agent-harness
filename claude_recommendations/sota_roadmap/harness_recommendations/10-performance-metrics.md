---
title: "Add Performance Metrics and Monitoring"
labels: medium-priority, observability, enhancement
priority: P2
---

## Problem Statement

No visibility into agent performance:
- Can't track execution speed
- No cost tracking per session
- Can't identify bottlenecks
- No performance degradation alerts
- Difficult to optimize without data

## Proposed Solution

Implement comprehensive performance tracking:

```python
class PerformanceTracker:
    """Track and analyze agent performance"""
    
    def __init__(self):
        self.metrics = {
            'total_steps': 0,
            'total_time': 0.0,
            'tool_calls': defaultdict(int),
            'tool_times': defaultdict(list),
            'total_tokens': 0,
            'total_cost': 0.0,
            'errors': 0,
            'success_rate': 0.0,
            'context_compressions': 0
        }
        self.step_history = []
        
    def record_step(self, step_data: dict):
        """Record a single step's metrics"""
        self.metrics['total_steps'] += 1
        self.metrics['total_time'] += step_data.get('duration', 0)
        
        if tokens := step_data.get('tokens'):
            self.metrics['total_tokens'] += tokens
            self.metrics['total_cost'] += self._calculate_cost(tokens)
        
        self.step_history.append(step_data)
        
    def record_tool_call(self, tool: str, duration: float):
        """Record tool execution time"""
        self.metrics['tool_calls'][tool] += 1
        self.metrics['tool_times'][tool].append(duration)
        
    def get_summary(self) -> dict:
        """Get performance summary"""
        return {
            'total_steps': self.metrics['total_steps'],
            'total_time': f"{self.metrics['total_time']:.2f}s",
            'avg_step_time': self._avg_step_time(),
            'total_tokens': self.metrics['total_tokens'],
            'estimated_cost': f"${self.metrics['total_cost']:.4f}",
            'most_used_tool': max(self.metrics['tool_calls'], key=self.metrics['tool_calls'].get),
            'success_rate': f"{self._calculate_success_rate():.1%}"
        }
        
    def get_tool_stats(self) -> dict:
        """Get per-tool statistics"""
        stats = {}
        for tool, times in self.metrics['tool_times'].items():
            stats[tool] = {
                'calls': len(times),
                'avg_time': np.mean(times),
                'max_time': max(times),
                'total_time': sum(times)
            }
        return stats
```

## Key Metrics

### Execution Metrics
- Total steps
- Total execution time
- Average time per step
- Time distribution (percentiles)
- Slowest steps

### Tool Metrics
- Calls per tool
- Execution time per tool
- Success/failure rate per tool
- Most/least used tools

### Cost Metrics
```python
class CostTracker:
    """Track API costs"""
    
    PRICING = {
        'claude-sonnet-4-20250514': {
            'input': 3.00 / 1_000_000,   # per token
            'output': 15.00 / 1_000_000,
            'cache_write': 3.75 / 1_000_000,
            'cache_read': 0.30 / 1_000_000
        },
        'gpt-4-turbo': {
            'input': 10.00 / 1_000_000,
            'output': 30.00 / 1_000_000
        }
    }
    
    def calculate_cost(self, model: str, usage: dict) -> float:
        """Calculate cost for a request"""
        pricing = self.PRICING.get(model, {})
        
        cost = 0.0
        cost += usage.get('input_tokens', 0) * pricing.get('input', 0)
        cost += usage.get('output_tokens', 0) * pricing.get('output', 0)
        cost += usage.get('cache_write_tokens', 0) * pricing.get('cache_write', 0)
        cost += usage.get('cache_read_tokens', 0) * pricing.get('cache_read', 0)
        
        return cost
```

### Context Metrics
- Current context size (tokens)
- Max context used
- Compression events
- Cache hits/misses
- Token usage over time

### Quality Metrics
- Success rate (completed vs failed)
- Error frequency
- Retry count
- Human intervention rate

## Implementation Details

### 1. Create PerformanceTracker Class
(`src/agent_harness/metrics.py`)

### 2. Integrate with Harness
```python
class AgentHarness:
    def __init__(self, ...):
        self.metrics = PerformanceTracker()
        
    def _execute_step(self, ...):
        start = time.time()
        result = self._do_step(...)
        duration = time.time() - start
        
        self.metrics.record_step({
            'duration': duration,
            'tokens': result.usage.total_tokens,
            'success': result.success
        })
```

### 3. Add Real-Time Dashboard
```python
class MetricsDashboard:
    """Display metrics in real-time"""
    
    def __init__(self, tracker: PerformanceTracker):
        self.tracker = tracker
        
    def display(self):
        """Print current metrics"""
        clear_screen()
        print("╔══════════════════════════════════════╗")
        print("║      Agent Performance Metrics       ║")
        print("╠══════════════════════════════════════╣")
        print(f"║ Steps:          {self.tracker.metrics['total_steps']:>15} ║")
        print(f"║ Time:           {self.tracker.metrics['total_time']:>12.2f}s ║")
        print(f"║ Tokens:         {self.tracker.metrics['total_tokens']:>15} ║")
        print(f"║ Cost:          ${self.tracker.metrics['total_cost']:>15.4f} ║")
        print("╚══════════════════════════════════════╝")
```

### 4. Export Capabilities
```python
def export_metrics(self, format: str = 'json'):
    """Export metrics for analysis"""
    if format == 'json':
        return json.dumps(self.metrics)
    elif format == 'csv':
        return self._to_csv()
    elif format == 'prometheus':
        return self._to_prometheus()
```

### 5. Alerts and Thresholds
```python
class PerformanceAlert:
    """Alert on performance issues"""
    
    THRESHOLDS = {
        'max_step_time': 30.0,  # seconds
        'max_cost_per_step': 0.10,  # dollars
        'max_context_size': 150_000,  # tokens
        'min_success_rate': 0.80  # 80%
    }
    
    def check_thresholds(self, metrics: dict):
        """Alert if thresholds exceeded"""
        alerts = []
        
        if metrics['avg_step_time'] > self.THRESHOLDS['max_step_time']:
            alerts.append(f"⚠️  Slow steps: {metrics['avg_step_time']:.1f}s")
        
        if metrics['cost_per_step'] > self.THRESHOLDS['max_cost_per_step']:
            alerts.append(f"⚠️  High cost: ${metrics['cost_per_step']:.4f}/step")
        
        return alerts
```

## Visualization

### CLI Output
```
Session Performance Summary
===========================
Duration:     5m 23s
Steps:        47
Success Rate: 91.5%

Tool Usage:
  edit_file:     23 calls (2.3s avg)
  read_file:     15 calls (0.8s avg)
  run_tests:      6 calls (4.5s avg)
  bash:           3 calls (1.2s avg)

Cost Breakdown:
  Input tokens:  125,430 ($0.3763)
  Output tokens:  23,450 ($0.3518)
  Cache reads:    45,200 ($0.0136)
  Total:                  $0.7417

Slowest Steps:
  1. Step 23: Run full test suite (12.3s)
  2. Step 15: Read large file (8.7s)
  3. Step 31: Complex refactor (6.4s)
```

### Export to CSV
```csv
step,duration,tokens,cost,tool,success
1,2.3,1240,0.0186,edit_file,true
2,0.8,450,0.0068,read_file,true
3,4.5,2340,0.0351,run_tests,false
```

### Integration with Monitoring Tools
```python
# Prometheus metrics
harness_steps_total{status="success"} 42
harness_steps_total{status="failure"} 5
harness_step_duration_seconds{quantile="0.5"} 2.3
harness_step_duration_seconds{quantile="0.95"} 8.7
harness_cost_dollars_total 0.7417

# Datadog
statsd.increment('harness.steps')
statsd.timing('harness.step.duration', duration)
statsd.gauge('harness.context.tokens', token_count)
```

## Configuration

```python
metrics_config = {
    'enabled': True,
    'track_costs': True,
    'track_tools': True,
    'track_context': True,
    'export_format': 'json',  # or 'csv', 'prometheus'
    'export_interval': 60,  # seconds
    'dashboard': {
        'enabled': True,
        'update_interval': 5  # seconds
    },
    'alerts': {
        'enabled': True,
        'thresholds': {
            'max_step_time': 30.0,
            'max_cost': 1.00,
            'min_success_rate': 0.80
        }
    }
}
```

## Acceptance Criteria

- [ ] Tracks all key metrics (time, cost, tokens, success)
- [ ] Per-tool statistics available
- [ ] Cost calculation accurate for all providers
- [ ] Real-time dashboard displays
- [ ] Export to JSON/CSV works
- [ ] Alerts trigger on thresholds
- [ ] Performance summary at session end
- [ ] Minimal overhead (<2%)
- [ ] Documentation includes metric definitions
- [ ] Examples show metric usage

## Dependencies

- Issue #1 (Multi-Provider) - for cost tracking
- Issue #6 (Trajectory Logging) - complements logging

## Estimated Effort

Small (3-4 days)

## Future Enhancements

- Grafana dashboards
- Historical trending
- A/B test comparison
- Anomaly detection
- Cost optimization suggestions
- Performance regression detection
