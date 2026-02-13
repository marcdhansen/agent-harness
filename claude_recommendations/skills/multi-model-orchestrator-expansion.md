# Multi-Model Orchestrator Skill - Complete Implementation

## Purpose

Expand the brief multi-model orchestrator into a fully functional system for routing tasks to specialized agent roles optimized for different LLM models.

## Integration

Replace the existing multi-model-orchestrator/SKILL.md with this comprehensive version:

---

# 🎭 Multi-Model Orchestrator Skill

**Purpose**: Route tasks to specialized agent roles running on optimal LLM models for maximum efficiency and quality.

## 🎯 Mission

- Route tasks to specialized agents based on task type
- Leverage model-specific strengths (speed, reasoning, coding)
- Synthesize results from multiple agents
- Provide fallback mechanisms
- Track performance metrics

## 👥 Agent Roles & Model Optimization

### 1. Sisyphus (Strategic Lead)
**Optimal Model**: Gemini 1.5 Pro (2M context)  
**Specialization**: Strategy, planning, broad context handling

**Strengths**:
- Massive context window (2M tokens)
- Excellent at connecting disparate information
- Strong architectural thinking
- Good at long-term planning

**Task Types**:
- Feature planning and architecture
- Code review (broad perspective)
- Refactoring strategies
- Documentation synthesis
- Cross-module impact analysis

**Example Invocation**:
```bash
/multi-model --role sisyphus \
  --task "Plan architecture for real-time notification system" \
  --context "Full codebase context required"
```

### 2. Hephaestus (Fast Coder)
**Optimal Model**: qwen2.5-coder (32B)  
**Specialization**: High-speed code implementation

**Strengths**:
- Extremely fast code generation
- Strong coding patterns knowledge
- Good at following specifications
- Efficient refactoring

**Task Types**:
- Implementing well-specified features
- Code refactoring
- Writing boilerplate
- Test generation
- Quick bug fixes

**Example Invocation**:
```bash
/multi-model --role hephaestus \
  --task "Implement UserAuth class per spec" \
  --spec-file "specs/user_auth.md"
```

### 3. Oracle (Validator)
**Optimal Model**: Claude 3.5 Sonnet  
**Specialization**: Logic verification, security audit

**Strengths**:
- Excellent reasoning capabilities
- Strong at finding edge cases
- Security-aware
- Good at identifying bugs

**Task Types**:
- Code review (logic verification)
- Security audits
- Bug finding
- Test case generation
- Algorithm verification

**Example Invocation**:
```bash
/multi-model --role oracle \
  --task "Review authentication logic for vulnerabilities" \
  --files "src/auth/*.py"
```

### 4. Librarian (Knowledge Retrieval)
**Optimal Model**: GPT-4o-mini  
**Specialization**: Fast documentation search and retrieval

**Strengths**:
- Fast and cost-effective
- Good at finding relevant docs
- Strong at summarization
- Efficient context extraction

**Task Types**:
- Documentation lookup
- API reference retrieval
- Example code finding
- Quick fact-checking
- Issue tracking searches

**Example Invocation**:
```bash
/multi-model --role librarian \
  --task "Find examples of JWT token validation in codebase" \
  --search-depth "comprehensive"
```

## 🔄 Task Routing System

### Automatic Task Classification

```python
#!/usr/bin/env python3
# scripts/route_task.py

import argparse
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class AgentRole(Enum):
    SISYPHUS = "sisyphus"
    HEPHAESTUS = "hephaestus"
    ORACLE = "oracle"
    LIBRARIAN = "librarian"

class TaskType(Enum):
    PLANNING = "planning"
    CODING = "coding"
    REVIEW = "review"
    SEARCH = "search"

@dataclass
class TaskRoute:
    role: AgentRole
    model: str
    reasoning: str

def classify_task(task_description: str) -> TaskType:
    """Classify task based on description keywords"""
    
    planning_keywords = ['plan', 'architect', 'design', 'strategy', 'refactor']
    coding_keywords = ['implement', 'code', 'write', 'create', 'build']
    review_keywords = ['review', 'audit', 'verify', 'check', 'validate']
    search_keywords = ['find', 'search', 'lookup', 'locate', 'example']
    
    task_lower = task_description.lower()
    
    if any(kw in task_lower for kw in planning_keywords):
        return TaskType.PLANNING
    elif any(kw in task_lower for kw in review_keywords):
        return TaskType.REVIEW
    elif any(kw in task_lower for kw in search_keywords):
        return TaskType.SEARCH
    elif any(kw in task_lower for kw in coding_keywords):
        return TaskType.CODING
    
    # Default: treat as coding task
    return TaskType.CODING

def route_task(task_description: str, 
               task_type: Optional[TaskType] = None) -> TaskRoute:
    """Route task to appropriate agent role"""
    
    if task_type is None:
        task_type = classify_task(task_description)
    
    routing = {
        TaskType.PLANNING: TaskRoute(
            role=AgentRole.SISYPHUS,
            model="gemini-1.5-pro",
            reasoning="Strategic planning requires broad context and architectural thinking"
        ),
        TaskType.CODING: TaskRoute(
            role=AgentRole.HEPHAESTUS,
            model="qwen2.5-coder:32b",
            reasoning="Implementation task needs fast, efficient code generation"
        ),
        TaskType.REVIEW: TaskRoute(
            role=AgentRole.ORACLE,
            model="claude-3-5-sonnet-20241022",
            reasoning="Validation requires strong reasoning and bug detection"
        ),
        TaskType.SEARCH: TaskRoute(
            role=AgentRole.LIBRARIAN,
            model="gpt-4o-mini",
            reasoning="Search task benefits from fast, cost-effective retrieval"
        )
    }
    
    return routing[task_type]

def main():
    parser = argparse.ArgumentParser(description='Route task to optimal agent')
    parser.add_argument('--task', required=True, help='Task description')
    parser.add_argument('--role', choices=[r.value for r in AgentRole], 
                       help='Force specific role (skip auto-routing)')
    
    args = parser.parse_args()
    
    if args.role:
        role = AgentRole(args.role)
        print(f"Manual routing to: {role.value}")
    else:
        route = route_task(args.task)
        print(f"Auto-routing to: {route.role.value}")
        print(f"Model: {route.model}")
        print(f"Reasoning: {route.reasoning}")

if __name__ == "__main__":
    main()
```

### Multi-Agent Workflow

```bash
#!/bin/bash
# scripts/multi_agent_workflow.sh

# Example: Feature implementation with multiple agents

FEATURE="Add user authentication"

echo "=== PHASE 1: PLANNING (Sisyphus) ==="
python scripts/route_task.py --role sisyphus --task "Plan architecture for: $FEATURE"

# Sisyphus generates plan.md
# - Database schema
# - API endpoints
# - Security considerations
# - Implementation steps

echo ""
echo "=== PHASE 2: IMPLEMENTATION (Hephaestus) ==="
python scripts/route_task.py --role hephaestus --task "Implement authentication per plan"

# Hephaestus implements code
# - Fast code generation
# - Follows plan specifications
# - Writes tests

echo ""
echo "=== PHASE 3: VALIDATION (Oracle) ==="
python scripts/route_task.py --role oracle --task "Review authentication implementation"

# Oracle reviews code
# - Checks for security issues
# - Validates logic
# - Identifies edge cases

echo ""
echo "=== PHASE 4: DOCUMENTATION (Librarian) ==="
python scripts/route_task.py --role librarian --task "Find and document auth examples"

# Librarian adds documentation
# - Usage examples
# - API reference
# - Integration guide

echo ""
echo "=== SYNTHESIS ==="
echo "All phases complete. Review outputs in:"
echo "- plan.md (Sisyphus)"
echo "- src/auth/ (Hephaestus)"
echo "- review_report.md (Oracle)"
echo "- docs/auth.md (Librarian)"
```

## 🔀 Result Synthesis

### Combining Agent Outputs

```python
# scripts/synthesize_results.py

from typing import List, Dict

def synthesize_planning_and_implementation(
    plan: str,  # From Sisyphus
    implementation: str  # From Hephaestus
) -> str:
    """Synthesize plan and implementation into cohesive result"""
    
    synthesis = f"""
# Feature Implementation Summary

## Original Plan (Sisyphus)
{plan}

## Implementation Details (Hephaestus)
{implementation}

## Verification Status
- Plan followed: {'Yes' if verify_plan_followed(plan, implementation) else 'No'}
- All requirements met: {'Yes' if check_requirements(plan, implementation) else 'No'}
- Code quality: {assess_code_quality(implementation)}

## Next Steps
- Oracle review recommended
- Documentation update needed
- Integration testing required
"""
    return synthesis

def synthesize_review_feedback(
    implementation: str,  # From Hephaestus
    review: str  # From Oracle
) -> str:
    """Combine implementation with review feedback"""
    
    issues = extract_issues(review)
    
    if not issues:
        return f"""
✅ Code Review Passed

Implementation is ready to merge.

{implementation}

Review Notes:
{review}
"""
    
    return f"""
⚠️ Code Review - Issues Found

Implementation needs updates.

Issues to Address:
{format_issues(issues)}

Original Implementation:
{implementation}

Detailed Review:
{review}
"""
```

## 🎯 Model-Specific Optimizations

### Gemini 1.5 Pro (Sisyphus) Optimizations

```python
# Use full codebase context
context_files = [
    "src/**/*.py",
    "docs/**/*.md",
    "tests/**/*.py"
]

# Leverage 2M token window
prompt = f"""
Given the entire codebase (included below), plan the architecture for {feature}.

<codebase>
{load_all_files(context_files)}
</codebase>

Consider:
- Existing patterns and conventions
- Impact on other modules
- Security implications
- Testing strategy
"""
```

### qwen2.5-coder (Hephaestus) Optimizations

```python
# Optimize for speed with clear specifications
prompt = f"""
Implement the following specification:

{load_spec('specs/feature.md')}

Requirements:
- Follow existing code style
- Include docstrings
- Write unit tests
- Handle edge cases

Generate complete, working code.
"""
```

### Claude 3.5 Sonnet (Oracle) Optimizations

```python
# Leverage strong reasoning for deep analysis
prompt = f"""
Review this implementation for logic errors and security issues:

<implementation>
{load_implementation()}
</implementation>

Analyze:
1. Logic correctness (are there bugs?)
2. Security vulnerabilities (SQL injection, XSS, etc.)
3. Edge cases (what happens when...?)
4. Performance issues (inefficient algorithms?)
5. Code quality (maintainability, readability)

For each issue found:
- Severity: LOW/MEDIUM/HIGH/CRITICAL
- Location: File and line number
- Description: What's wrong
- Recommendation: How to fix
"""
```

### GPT-4o-mini (Librarian) Optimizations

```python
# Optimize for cost and speed
prompt = f"""
Find examples of {pattern} in the codebase.

Search in: {search_paths}

Return:
- File path
- Line numbers
- Code snippet (5 lines context)
- Brief explanation

Limit to 5 most relevant examples.
"""
```

## 📊 Performance Tracking

```python
# scripts/track_performance.py

import json
from datetime import datetime
from pathlib import Path

class PerformanceTracker:
    def __init__(self):
        self.metrics_file = Path(".agent/multi_model_metrics.json")
        self.metrics = self.load_metrics()
    
    def track_task(self, role: str, task: str, duration: float, 
                   tokens_used: int, success: bool):
        """Track agent performance"""
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "task_type": classify_task(task).value,
            "duration_seconds": duration,
            "tokens_used": tokens_used,
            "success": success
        }
        
        self.metrics.setdefault(role, []).append(entry)
        self.save_metrics()
    
    def generate_report(self):
        """Generate performance report"""
        
        report = "# Multi-Model Agent Performance\n\n"
        
        for role, entries in self.metrics.items():
            total_tasks = len(entries)
            successful = sum(1 for e in entries if e['success'])
            avg_duration = sum(e['duration_seconds'] for e in entries) / total_tasks
            total_tokens = sum(e['tokens_used'] for e in entries)
            
            report += f"## {role.upper()}\n"
            report += f"- Tasks: {total_tasks}\n"
            report += f"- Success Rate: {successful/total_tasks*100:.1f}%\n"
            report += f"- Avg Duration: {avg_duration:.2f}s\n"
            report += f"- Total Tokens: {total_tokens:,}\n\n"
        
        return report
```

## 🛡️ Fallback Mechanisms

```python
# scripts/multi_model_with_fallback.py

def execute_with_fallback(task: str, preferred_role: AgentRole) -> str:
    """Execute task with fallback to other agents"""
    
    try:
        # Try preferred agent
        result = execute_agent(preferred_role, task)
        if result.success:
            return result.output
    except Exception as e:
        log_error(f"{preferred_role} failed: {e}")
    
    # Fallback sequence
    fallback_sequence = get_fallback_sequence(preferred_role)
    
    for fallback_role in fallback_sequence:
        try:
            log_info(f"Falling back to {fallback_role}")
            result = execute_agent(fallback_role, task)
            if result.success:
                return result.output
        except Exception as e:
            log_error(f"{fallback_role} failed: {e}")
            continue
    
    # Final fallback: primary model
    log_warning("All specialized agents failed, using primary model")
    return execute_primary_model(task)

def get_fallback_sequence(primary_role: AgentRole) -> List[AgentRole]:
    """Get fallback agents for each role"""
    
    fallbacks = {
        AgentRole.SISYPHUS: [AgentRole.ORACLE],  # Oracle can do planning
        AgentRole.HEPHAESTUS: [AgentRole.SISYPHUS],  # Sisyphus can code
        AgentRole.ORACLE: [AgentRole.SISYPHUS],  # Sisyphus can review
        AgentRole.LIBRARIAN: [AgentRole.SISYPHUS]  # Sisyphus can search
    }
    
    return fallbacks.get(primary_role, [])
```

## ✅ Usage Examples

### Example 1: Feature Development

```bash
# Full feature implementation pipeline
/multi-model --pipeline feature \
  --name "user-notifications" \
  --description "Real-time user notifications via WebSocket"

# Automatically routes through:
# 1. Sisyphus: Plan architecture
# 2. Hephaestus: Implement code
# 3. Oracle: Review implementation
# 4. Librarian: Generate documentation
```

### Example 2: Bug Fix

```bash
# Bug investigation and fix
/multi-model --pipeline bugfix \
  --bug-id "ISSUE-123" \
  --description "Memory leak in parser"

# Routes through:
# 1. Sisyphus: Analyze bug and plan fix
# 2. Oracle: Verify analysis is correct
# 3. Hephaestus: Implement fix
# 4. Oracle: Verify fix works
```

### Example 3: Code Review

```bash
# Comprehensive code review
/multi-model --pipeline review \
  --files "src/auth/*.py" \
  --depth "comprehensive"

# Routes through:
# 1. Librarian: Find similar code examples
# 2. Oracle: Deep security and logic review
# 3. Sisyphus: Architectural assessment
```

## 📝 Configuration

```yaml
# config/multi_model.yaml

agents:
  sisyphus:
    model: "gemini-1.5-pro"
    api_key_env: "GEMINI_API_KEY"
    max_tokens: 2000000
    temperature: 0.7
  
  hephaestus:
    model: "qwen2.5-coder:32b"
    api_base: "http://localhost:11434"
    max_tokens: 32768
    temperature: 0.3  # Lower for code generation
  
  oracle:
    model: "claude-3-5-sonnet-20241022"
    api_key_env: "ANTHROPIC_API_KEY"
    max_tokens: 8192
    temperature: 0.5
  
  librarian:
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"
    max_tokens: 16384
    temperature: 0.3

routing:
  auto_classify: true
  allow_manual_override: true
  enable_fallback: true
  
performance:
  track_metrics: true
  metrics_file: ".agent/multi_model_metrics.json"
```

## 🔗 Integration Points

- **Orchestrator**: Multi-model execution within orchestrated workflows
- **Planning**: Sisyphus handles complex planning tasks
- **Code Review**: Oracle provides deep validation
- **Testing**: Hephaestus generates test cases efficiently

---

**Remember**: Different models have different strengths. Route tasks to leverage these strengths for maximum effectiveness.
