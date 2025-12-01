# Simplified MDB Architecture

## Overview

MDB has been **simplified** based on real-world testing that showed deterministic mode outperformed complex Bayesian refinement logic for clinical queries involving code generation and vision analysis.

## Key Changes

### 1. Simplified Parameters (Both Modes)

**Before** (8 parameters):
```python
Agent(
    persist_outputs=False,
    output_dir="./medster_outputs",
    enable_iterative_refinement=True,
    refinement_confidence_threshold=0.7,
    max_refinement_attempts=2,
    enable_confidence_early_stopping=True,
    early_stop_confidence_threshold=0.90,
    early_stop_uncertainty_threshold=1.0
)
```

**After** (3 parameters):
```python
Agent(
    persist_outputs=False,
    output_dir="./medster_outputs",
    enable_simple_refinement=True,      # Works for both modes
    max_refinement_attempts=1           # Just 1 retry (not 2)
)
```

### 2. Simplified Validation Logic

**Bayesian Mode**:
- ✅ **Keeps**: Confidence tracking (logs for visibility, doesn't block)
- ✅ **Keeps**: Meta-validation with confidence (for monitoring)
- ❌ **Removed**: Complex confidence-based refinement (caused stalling)
- ❌ **Removed**: Early stopping logic (never triggered in practice)
- ✅ **Added**: Simple one-retry refinement (like deterministic mode)

**Deterministic Mode**:
- ✅ **Keeps**: Binary validation (done: true/false)
- ✅ **Keeps**: Simple meta-validation
- ✅ **Added**: Simple one-retry refinement (Dexter pattern for data endpoints)

### 3. Unified Refinement Pattern

**Both modes now use the same simple refinement**:
```python
# If task not done and we have retries left, try once more
if not is_done and enable_simple_refinement and per_task_steps <= max_refinement_attempts:
    logger.log("🔄 Task incomplete, retrying once...")
    continue  # Retry task
```

**When it helps**:
- Data retrieval with wrong parameters (e.g., missing date_range)
- Incomplete results on first attempt (e.g., partial lab panel)
- Connection timeouts or temporary failures

**When it doesn't help** (no retry needed):
- Code generation tasks (results vary by nature)
- Vision analysis (subjective interpretation)
- Data truly doesn't exist (refinement can't create data)

## Performance Comparison

| Feature | Old Bayesian | New Bayesian | Deterministic |
|---------|--------------|--------------|---------------|
| **Confidence Tracking** | ✅ (blocks execution) | ✅ (logs only) | ❌ |
| **Refinement** | Complex (confidence < 0.7) | Simple (task incomplete) | Simple (task incomplete) |
| **Early Stopping** | ✅ (complex uncertainty calc) | ❌ | ❌ |
| **Max Retries** | 2 attempts | 1 attempt | 1 attempt |
| **Speed** | Slowest | Fast | Fastest |
| **Complexity** | High | Low | Lowest |
| **Best For** | Research queries | General use | Complex queries |

## CLI Usage

### Basic Usage (Default)
```bash
uv run medster-agent
# Simple refinement: ✅ enabled (1 retry)
# Task persistence: ❌ disabled
```

### Enable Task Persistence
```bash
uv run medster-agent --persist
# Saves JSON logs to: ./medster_outputs/task_1_output.json, task_2_output.json, ...
```

### Disable Refinement
```bash
uv run medster-agent --no-refinement
# No retries - tasks either complete or fail on first attempt
```

### Combined Options
```bash
uv run medster-agent --persist --no-refinement
```

## Task Persistence Output Format

**Location**: `./medster_outputs/`

**Files**: `task_1_output.json`, `task_2_output.json`, ...

**Deterministic Mode**:
```json
{
  "task_id": 1,
  "task_description": "Get patient labs for troponin",
  "timestamp": "2025-12-01T13:45:30.123456",
  "outputs": ["Tool results..."],
  "reasoning_mode": "deterministic"
}
```

**Bayesian Mode** (includes confidence metadata):
```json
{
  "task_id": 1,
  "task_description": "Get patient labs for troponin",
  "timestamp": "2025-12-01T13:45:30.123456",
  "outputs": ["Tool results..."],
  "metadata": {
    "confidence": 0.95,
    "data_completeness": 1.0,
    "uncertainty_factors": []
  },
  "reasoning_mode": "bayesian"
}
```

## Example Execution Flow

### Deterministic Mode (Simplified)
```
✓ Planning clinical analysis ✓
  Tasks planned

  [TASK 1] Get patient labs
  Fetching get_patient_labs...
  ⠋ Checking if task is complete...
  ✓ Task complete
  📁 Saved task 1 output to: ./medster_outputs/task_1_output.json  (if --persist)

  [TASK 2] Get ECG findings
  Fetching generate_and_run_analysis...
  ⠋ Checking if task is complete...
  🔄 Task incomplete, retrying once... (attempt 2/2)
  Fetching generate_and_run_analysis...
  ✓ Task complete

  ⠋ Checking if analysis is complete...
  ✓ Clinical analysis complete ✓

  Generating clinical summary...
```

### Bayesian Mode (Simplified)
```
✓ Planning clinical analysis ✓
  Tasks planned

  [TASK 1] Get patient labs
  Fetching get_patient_labs...
  ⠋ Checking if task is complete...
  ✓ Task complete: confidence=0.95, data_completeness=1.0
  📁 Saved task 1 output with confidence metadata (if --persist)

  [TASK 2] Get ECG findings
  Fetching generate_and_run_analysis...
  ⠋ Checking if task is complete...
  🔄 Task incomplete, retrying once... (attempt 2/2)
  Fetching generate_and_run_analysis...
  ✓ Task complete: confidence=0.88, data_completeness=0.95

  ⠋ Checking if analysis is complete...
  Goal achieved (confidence=0.92). Generating summary.
```

## Architecture Decisions

### Why We Simplified

1. **Real-world testing showed deterministic mode was faster** for complex queries (vision + code generation)
2. **Bayesian refinement caused stalling** when confidence scores were unreliable (code generation tasks)
3. **Early stopping never triggered** in practice (confidence rarely reached 0.90 for complex queries)
4. **Complexity without benefit** - 8 parameters managing features that didn't help

### What We Kept

1. ✅ **Exception handling** - Prevents crashes, robust error recovery
2. ✅ **Task persistence** - Useful for debugging (optional via `--persist`)
3. ✅ **Confidence tracking** (Bayesian mode) - Logs confidence for visibility, doesn't block
4. ✅ **Simple refinement** (both modes) - One retry helps with data retrieval issues

### What We Removed

1. ❌ **Complex confidence thresholds** - `refinement_confidence_threshold=0.7`
2. ❌ **Multi-attempt refinement** - Reduced from 2 to 1 retry
3. ❌ **Early stopping thresholds** - `early_stop_confidence_threshold`, `early_stop_uncertainty_threshold`
4. ❌ **Blocking on confidence** - Refinement no longer depends on confidence scores

## Dexter-Inspired Refinement for Deterministic Data

**Key Insight**: Refinement makes MORE sense for deterministic data endpoints than for analytical/generative tasks.

### Works Well For (Dexter Pattern)
- **Financial data** (Dexter's domain): "Get stock price" → retry with different date range
- **Clinical data** (Medster's domain): "Get patient labs" → retry with different parameters
- **Deterministic validation**: Either you got the data or you didn't (binary)

### Doesn't Work Well For
- **Code generation**: Results vary, hard to validate what "better" means
- **Vision analysis**: Subjective interpretation, confidence scores unreliable
- **Complex reasoning**: Multiple valid approaches, refinement doesn't help

## Recommendations

### Use Deterministic Mode (Default) For:
- General clinical case analysis
- Complex queries with vision analysis
- Queries requiring code generation
- Production use cases

### Use Bayesian Mode For:
- Research requiring confidence tracking
- Queries where you want to monitor data quality
- Cases where uncertainty quantification matters
- Debugging data retrieval issues

### Enable Task Persistence (`--persist`) For:
- Debugging long-running analyses
- Auditing clinical decisions
- Session resumption (future feature)
- Understanding what data was actually retrieved

### Disable Refinement (`--no-refinement`) For:
- Maximum speed (no retries)
- Cases where first attempt should be definitive
- Testing tool behavior

---

**Result**: Simpler, faster, more robust agent that works better for real-world clinical queries while preserving the useful parts of the Dexter-inspired enhancements.
