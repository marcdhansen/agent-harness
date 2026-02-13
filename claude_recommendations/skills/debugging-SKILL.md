---
name: debugging
description: Systematic debugging approaches, tools, and techniques for identifying and fixing bugs efficiently. Covers reproduction, isolation, debugging tools, and common debugging patterns.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Glob, Grep
---

# 🐛 Debugging Skill

**Purpose**: Guide agents through systematic debugging processes to identify and fix bugs efficiently.

## 🎯 Mission

- Debug issues systematically (not trial-and-error)
- Use appropriate debugging tools effectively
- Isolate problems quickly
- Fix root causes (not just symptoms)
- Prevent similar bugs in the future

## 📋 When to Use This Skill

Use this skill when:
- Code produces unexpected output
- Tests are failing
- Application crashes or hangs
- Performance issues occur
- Behavior differs from specification
- Integration problems arise

## 🔬 Systematic Debugging Process

### Step 1: Reproduce the Bug Reliably

**Goal**: Create minimal, consistent reproduction

```python
# Bad: "Sometimes the parser crashes"
# Good: Minimal reproduction case

def reproduce_bug():
    """Minimal code that reliably triggers the bug"""
    data = '{"invalid": json'  # Specific input
    parser = JSONParser()
    result = parser.parse(data)  # Crashes here every time
    return result

# Test it
reproduce_bug()  # Should fail consistently
```

**Reproduction Checklist:**
- [ ] Bug occurs every time (not intermittent)
- [ ] Code is minimal (remove unrelated parts)
- [ ] Input data is minimal (simplest input that triggers bug)
- [ ] Environment is documented (Python version, OS, dependencies)

### Step 2: Isolate the Problem

**Goal**: Identify exactly where the bug occurs

```python
# Binary search through code execution

def test_step_1():
    """Test first part of pipeline"""
    data = load_data()
    assert data is not None  # ✅ Step 1 works
    
def test_step_2():
    """Test second part of pipeline"""
    data = load_data()
    processed = process_data(data)
    assert processed is not None  # ❌ Step 2 fails - bug is here!

def test_step_3():
    """Test third part of pipeline"""
    # Don't need to test - already know bug is in step 2
```

**Isolation Strategies:**
1. **Binary search**: Test middle of code path, then half again
2. **Comment out code**: Remove sections until bug disappears
3. **Add assertions**: Verify assumptions at each step
4. **Unit tests**: Test each function independently

### Step 3: Understand the Problem

**Goal**: Know exactly what's wrong before fixing

```python
# Ask these questions:
# 1. What did I expect to happen?
expected = {"status": "success", "data": [1, 2, 3]}

# 2. What actually happened?
actual = {"status": "error", "data": None}

# 3. Why is there a difference?
# - Missing null check?
# - Wrong data type?
# - Logic error?

# Document understanding
"""
Bug: process_data() returns None when input list is empty
Expected: Should return empty dict {"status": "success", "data": []}
Actual: Returns None (crashes downstream)
Root cause: Missing empty list handling
"""
```

### Step 4: Form Hypothesis

**Goal**: Predict what's wrong and how to test it

```python
# Hypothesis: Function crashes because it doesn't check for empty list

# Test hypothesis
def test_hypothesis():
    """Test if empty list is the problem"""
    # Test with empty list
    result = process_data([])  # Should crash if hypothesis correct
    
    # Test with non-empty list
    result = process_data([1])  # Should work if hypothesis correct

# If both tests confirm hypothesis, we understand the bug
```

### Step 5: Fix and Verify

**Goal**: Fix root cause and verify with tests

```python
# Before (buggy code)
def process_data(data):
    return {"status": "success", "data": data[0]}  # Crashes on empty list

# After (fixed code)
def process_data(data):
    if not data:  # Handle empty list
        return {"status": "success", "data": []}
    return {"status": "success", "data": data[0]}

# Verify fix with tests
def test_fix():
    # Test edge case that was broken
    result = process_data([])
    assert result == {"status": "success", "data": []}
    
    # Test normal case still works
    result = process_data([1, 2, 3])
    assert result == {"status": "success", "data": 1}
```

## 🛠️ Debugging Tools

### Print Debugging

**When**: Quick checks, simple scripts

```python
def process_data(data):
    print(f"DEBUG: Input type: {type(data)}, length: {len(data)}")
    print(f"DEBUG: Input data: {data}")
    
    result = transform(data)
    print(f"DEBUG: After transform: {result}")
    
    return result

# Better: Use logging instead of print
import logging
logging.basicConfig(level=logging.DEBUG)

def process_data(data):
    logging.debug(f"Input: {data}, Type: {type(data)}")
    result = transform(data)
    logging.debug(f"Output: {result}")
    return result
```

### Python Debugger (pdb)

**When**: Need to inspect variables, step through code

```python
import pdb

def buggy_function(data):
    # Set breakpoint
    pdb.set_trace()  # Execution pauses here
    
    # Or in Python 3.7+
    breakpoint()  # Cleaner syntax
    
    result = process(data)
    return result

# PDB Commands:
# n - next line
# s - step into function
# c - continue until next breakpoint
# p variable - print variable value
# pp variable - pretty-print variable
# l - list code around current line
# w - show where you are in call stack
# q - quit debugger
```

**Advanced PDB Usage:**

```python
# Conditional breakpoint
def process_items(items):
    for i, item in enumerate(items):
        if i == 5:  # Only break on 6th item
            breakpoint()
        process(item)

# Post-mortem debugging
import pdb

try:
    buggy_function()
except Exception:
    pdb.post_mortem()  # Debug at point of exception
```

### Logging

**When**: Production code, long-running processes

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Processing data: {data}")
    
    try:
        result = expensive_operation(data)
        logger.info(f"Operation succeeded: {result}")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise

# Log levels (in order of severity):
# DEBUG - Detailed info for debugging
# INFO - General informational messages
# WARNING - Something unexpected but not breaking
# ERROR - Error occurred, function failed
# CRITICAL - Serious error, program may crash
```

### Stack Traces

**When**: Exception occurred, need to understand call chain

```python
import traceback

try:
    buggy_function()
except Exception as e:
    print("Exception occurred:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()

# Reading stack traces (bottom-to-top):
"""
Traceback (most recent call last):
  File "main.py", line 10, in <module>
    process_data(input)            # 3. Called from main
  File "processor.py", line 15, in process_data
    result = transform(data)       # 2. Called from process_data
  File "transformer.py", line 8, in transform
    return data[100]               # 1. ERROR OCCURRED HERE
IndexError: list index out of range
"""
```

### Assertions

**When**: Verify assumptions during development

```python
def process_data(data):
    # Verify assumptions
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    assert len(data) > 0, "Data must not be empty"
    assert all(isinstance(x, int) for x in data), "All elements must be int"
    
    result = sum(data) / len(data)
    
    # Verify postconditions
    assert isinstance(result, float), "Result should be float"
    assert result >= 0, "Average should be non-negative"
    
    return result

# Assertions are removed in optimized mode (python -O)
# Use for development/testing, not production error handling
```

## 🔍 Common Bug Patterns

### Pattern 1: Off-by-One Errors

```python
# Bug: Index out of range
def get_last_items(data, n):
    return data[-n:]  # What if n == 0?

# Test edge cases
get_last_items([1, 2, 3], 0)  # Returns empty list ✓
get_last_items([1, 2, 3], 5)  # Works but returns more than requested
get_last_items([], 2)  # Returns [] ✓

# Fix: Validate input
def get_last_items(data, n):
    if n <= 0:
        return []
    return data[-n:]
```

### Pattern 2: Mutable Default Arguments

```python
# Bug: Default list is shared across all calls
def add_item(item, items=[]):  # ❌ DON'T DO THIS
    items.append(item)
    return items

add_item(1)  # Returns [1]
add_item(2)  # Returns [1, 2] - UNEXPECTED!

# Fix: Use None as default
def add_item(item, items=None):  # ✅ CORRECT
    if items is None:
        items = []
    items.append(item)
    return items
```

### Pattern 3: Variable Scope Issues

```python
# Bug: Using loop variable after loop
for i in range(10):
    process(i)

# Later...
print(f"Processed {i} items")  # i is still 9 from loop!

# Fix: Use explicit counter
count = 0
for i in range(10):
    process(i)
    count += 1

print(f"Processed {count} items")  # Clear intent
```

### Pattern 4: Type Confusion

```python
# Bug: Mixing types
def calculate_total(prices):
    total = 0
    for price in prices:
        total += price  # What if price is string?
    return total

calculate_total(["10", "20", "30"])  # Returns "0102030" - string concatenation!

# Fix: Validate types or convert
def calculate_total(prices):
    total = 0
    for price in prices:
        # Convert to float, fail fast if can't
        total += float(price)
    return total
```

### Pattern 5: Silent Failures

```python
# Bug: Exception caught but ignored
def process_items(items):
    for item in items:
        try:
            process(item)
        except Exception:
            pass  # Silent failure - debugging nightmare!

# Fix: Log exceptions
def process_items(items):
    for item in items:
        try:
            process(item)
        except Exception as e:
            logging.error(f"Failed to process {item}: {e}", exc_info=True)
            # Decide: continue, raise, or accumulate errors
```

## 🎯 Debugging Strategies by Problem Type

### Strategy 1: Crash/Exception Debugging

```python
# 1. Get stack trace
try:
    buggy_function()
except Exception:
    traceback.print_exc()

# 2. Identify line where crash occurs (bottom of stack trace)

# 3. Add breakpoint before crash
def buggy_function():
    # ...
    breakpoint()  # Stop right before crash line
    crashing_line()

# 4. Inspect variables
# In pdb: pp locals() to see all variables

# 5. Fix and verify
```

### Strategy 2: Wrong Output Debugging

```python
# 1. Identify expected vs actual
expected = [1, 2, 3, 4, 5]
actual = get_numbers()
print(f"Expected: {expected}")
print(f"Actual: {actual}")
print(f"Diff: {set(expected) - set(actual)}")

# 2. Add intermediate checks
def get_numbers():
    step1 = load_data()
    print(f"After load: {step1}")  # Check step 1
    
    step2 = filter_data(step1)
    print(f"After filter: {step2}")  # Check step 2
    
    step3 = transform_data(step2)
    print(f"After transform: {step3}")  # Check step 3
    
    return step3

# 3. Find where output diverges from expected
```

### Strategy 3: Performance Debugging

```python
import time
import cProfile

# Timing specific code
start = time.perf_counter()
slow_function()
duration = time.perf_counter() - start
print(f"Took {duration:.2f} seconds")

# Profiling entire program
cProfile.run('main()')

# Output shows which functions consume most time:
"""
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      100    2.500    0.025    2.500    0.025 slow_function
     1000    0.100    0.000    0.100    0.000 fast_function
"""

# Memory profiling
import tracemalloc

tracemalloc.start()
# ... run code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

### Strategy 4: Intermittent Bug Debugging

```python
# 1. Add extensive logging
logging.basicConfig(level=logging.DEBUG, filename='debug.log')

# 2. Log everything that might be relevant
def sometimes_fails():
    logging.debug(f"Input state: {get_state()}")
    logging.debug(f"Environment: {os.environ}")
    logging.debug(f"Random seed: {random.getstate()}")
    
    result = risky_operation()
    
    logging.debug(f"Result: {result}")
    return result

# 3. Run many times to catch failure
for i in range(1000):
    try:
        sometimes_fails()
    except Exception as e:
        logging.error(f"Failed on iteration {i}: {e}")
        # Now check debug.log to see what was different

# 4. Look for patterns in failures
# - Specific input values?
# - Time-related (race condition)?
# - System state (memory, disk)?
```

## 🔧 Advanced Debugging Techniques

### Technique 1: Binary Search Debugging

```bash
# Use git bisect to find commit that introduced bug

git bisect start
git bisect bad HEAD  # Current version has bug
git bisect good v1.0  # Version 1.0 was working

# Git will check out a commit in the middle
# Test if bug exists
# If bug exists:
git bisect bad

# If bug doesn't exist:
git bisect good

# Repeat until Git finds the exact commit
```

### Technique 2: Rubber Duck Debugging

```python
# Explain code line-by-line to rubber duck (or colleague)

def process_data(data):
    # "First, I take the input data"
    # "Then I loop through each item"
    for item in data:
        # "For each item, I transform it"
        result = transform(item)
        # "Wait - what if transform returns None?"  # BUG FOUND!
        use_result(result)
```

### Technique 3: Differential Debugging

```python
# Compare working vs broken versions

# Working version (v1.0)
def process_v1(data):
    return [x * 2 for x in data]

# Broken version (v2.0)
def process_v2(data):
    return [x ** 2 for x in data]  # Changed from * to **

# Test both with same input
test_data = [1, 2, 3, 4, 5]
print("v1:", process_v1(test_data))  # [2, 4, 6, 8, 10]
print("v2:", process_v2(test_data))  # [1, 4, 9, 16, 25]

# Identify the difference and determine if intentional
```

### Technique 4: Debugging by Simplification

```python
# Start with complex code
def complex_function(data, config, options, flags):
    # 100 lines of code
    # Bug somewhere in here
    pass

# Simplify to minimal version
def simple_function(data):
    # Remove all optional parameters
    # Remove all features except core one
    # 10 lines of code
    result = core_logic(data)
    return result

# If bug still occurs: it's in core logic
# If bug gone: it's in one of the removed features
# Add features back one at a time until bug returns
```

## ✅ Debugging Checklist

Before debugging:
- [ ] Can you reproduce the bug reliably?
- [ ] Do you have a minimal reproduction case?
- [ ] Is the environment documented?
- [ ] Do you have tests that demonstrate the bug?

During debugging:
- [ ] Have you checked the stack trace thoroughly?
- [ ] Have you verified your assumptions with assertions?
- [ ] Have you isolated the problem to a specific function?
- [ ] Have you checked for common patterns (off-by-one, type issues, etc.)?
- [ ] Have you checked git history for recent changes?

After fixing:
- [ ] Does the original test case pass?
- [ ] Have you added a regression test?
- [ ] Have you verified no new bugs introduced?
- [ ] Have you documented the root cause?
- [ ] Can similar bugs be prevented with better code?

## 🚫 Debugging Anti-Patterns

### ❌ Random Changes (Hope-Driven Debugging)

```python
# Bad: Change code randomly hoping it fixes the bug
def buggy_function(data):
    # return data[0]  # Try this?
    # return data[-1]  # Or this?
    return data[len(data)]  # Maybe this?

# Good: Understand the bug first, then fix
def fixed_function(data):
    if not data:  # Handle edge case
        return None
    return data[0]  # Return first element
```

### ❌ Not Reading Error Messages

```python
# Error says: "KeyError: 'username'"
# Bad: Ignore error message, guess at fix

# Good: Read error message
# "KeyError: 'username'" means dictionary key 'username' doesn't exist
def get_user(user_dict):
    # Fix: Check if key exists
    return user_dict.get('username', 'Anonymous')
```

### ❌ Debugging by Adding Features

```python
# Bad: Add more code to fix bug in existing code
def process(data):
    # Original buggy code
    result = buggy_logic(data)
    
    # Instead of fixing bug, add workaround
    if result is None:  # ❌ Treating symptom, not cause
        result = fallback_logic(data)
    
    return result

# Good: Fix the root cause
def process(data):
    # Fix buggy_logic itself
    result = fixed_logic(data)  # ✅ Fix cause
    return result
```

## 🔗 Integration with Other Skills

- **TDD Skill**: Write failing test first, then fix bug
- **Git Skill**: Use git bisect to find regression
- **Code Review Skill**: Prevention through review
- **Testing Skill**: Comprehensive tests catch bugs early

---

**Remember**: The goal of debugging is not just to fix this bug, but to understand it so well that you can prevent similar bugs in the future.
