# GPT-5.1 Integration Guide

## Overview

MDB now supports **dual LLM providers**: Claude (Anthropic) and GPT-5.1 (OpenAI). You can easily switch between providers via environment variables.

## Quick Start

### Enable GPT-5.1

Edit `.env` file:
```bash
# LLM Provider Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.1

# OpenAI API Key
OPENAI_API_KEY=sk-proj-your-key-here

# GPT-5.1 Reasoning Effort (default: none for low latency)
REASONING_EFFORT=none
```

### Run with GPT-5.1

```bash
uv run medster-agent
```

The banner will show:
```
Powered by: GPT-5.1 (reasoning: none) + Coherent FHIR + MCP Medical Server
```

---

## GPT-5.1 Features

### Reasoning Effort Parameter

GPT-5.1 introduces a `reasoning.effort` parameter that controls how many reasoning tokens the model generates before producing a response.

**Options**:
- `none` (default) - **Fastest**, minimal reasoning, lowest latency
- `low` - Light reasoning, balanced speed
- `medium` - Moderate reasoning, thorough analysis
- `high` - **Most thorough**, deepest reasoning, highest latency

**Configuration** (`.env`):
```bash
REASONING_EFFORT=none    # Fast responses (default)
REASONING_EFFORT=low     # Light reasoning
REASONING_EFFORT=medium  # Moderate reasoning
REASONING_EFFORT=high    # Deep reasoning
```

### When to Use Each Setting

**`none` (Default - Recommended)**:
- Fast clinical queries requiring quick responses
- Data retrieval tasks (labs, vitals, demographics)
- Simple validation tasks
- General clinical case analysis
- **Best for Medster** - Matches deterministic mode speed

**`low`**:
- Clinical reasoning requiring light analysis
- Differential diagnosis with clear findings
- Risk stratification with standard criteria

**`medium`**:
- Complex clinical cases requiring deeper analysis
- Diagnostic uncertainty requiring thorough reasoning
- Multi-step clinical decision-making

**`high`**:
- Research queries requiring comprehensive analysis
- Complex differential diagnosis with rare conditions
- Clinical guidelines interpretation requiring careful reasoning
- **Caution**: Significantly slower, use only when necessary

---

## Model Comparison

| Feature | Claude Sonnet 4.5 | GPT-5.1 |
|---------|------------------|---------|
| **Provider** | Anthropic | OpenAI |
| **Context Window** | 200K tokens | 200K tokens |
| **Vision Support** | ✅ Yes | ✅ Yes |
| **Tool Calling** | ✅ Yes | ✅ Yes |
| **Reasoning Control** | ❌ No | ✅ Yes (effort parameter) |
| **Cost** | Moderate | Moderate |
| **Speed (none)** | Fast | Fast |
| **Speed (high)** | N/A | Slow |
| **Clinical Performance** | Excellent | Excellent |
| **Best For** | Complex reasoning | Steerability + reasoning |

---

## Configuration Examples

### GPT-5.1 (Fast Mode - Recommended)
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.1
REASONING_EFFORT=none
```

### GPT-5.1 (Deep Reasoning Mode)
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.1
REASONING_EFFORT=high
```

### GPT-5 (Original Reasoning Model)
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5
REASONING_EFFORT=medium  # Default for GPT-5
```

### GPT-4o (Vision + Fast)
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
# Note: GPT-4o doesn't support reasoning.effort parameter
```

### Claude Sonnet 4.5 (Default)
```bash
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-4.5
```

---

## Implementation Details

### Auto-Detection

The `call_llm()` function automatically detects the provider from the model name:

**OpenAI models** (starts with `gpt` or `o1`):
- `gpt-5.1` → OpenAI API
- `gpt-5` → OpenAI API
- `gpt-4o` → OpenAI API
- `o1` → OpenAI API

**Claude models** (all others):
- `claude-sonnet-4.5` → Anthropic API
- `claude-opus-4.5` → Anthropic API
- `claude-haiku-4` → Anthropic API

### Vision Support

Both providers support vision analysis (ECG waveforms, DICOM images):

**Claude format**:
```python
{
  "type": "image",
  "source": {
    "type": "base64",
    "media_type": "image/png",
    "data": img_base64
  }
}
```

**OpenAI format**:
```python
{
  "type": "image_url",
  "image_url": {
    "url": f"data:image/png;base64,{img_base64}"
  }
}
```

The model layer handles format conversion automatically.

### Structured Output

Both providers support structured output via Pydantic schemas:

```python
from pydantic import BaseModel

class ValidationResult(BaseModel):
    done: bool
    confidence: float

result = call_llm(
    prompt="Validate task completion",
    model="gpt-5.1",  # or "claude-sonnet-4.5"
    output_schema=ValidationResult
)
```

---

## Testing GPT-5.1 vs Claude

### Test Setup

**Test Query**:
```
Find patients with both hypertension and atrial fibrillation, analyze their ECG waveforms to confirm AFib patterns, and assess acute coronary risk factors
```

**Expected Behavior**:
- Task 1: Identify patients with both conditions
- Task 2: ECG vision analysis (multimodal)
- Task 3: Acute coronary risk assessment

### Performance Metrics to Compare

| Metric | Claude Sonnet 4.5 | GPT-5.1 (none) | GPT-5.1 (high) |
|--------|------------------|----------------|----------------|
| **Total Time** | ~4 min | ? | ? |
| **Task 1 Time** | 2.26s | ? | ? |
| **Task 2 Time** | 109s | ? | ? |
| **Task 3 Time** | 0.02s | ? | ? |
| **Vision Quality** | Excellent | ? | ? |
| **Code Generation** | Excellent | ? | ? |
| **Cost** | ~$0.04 | ? | ? |

### Run Comparison Test

```bash
# Test 1: Claude Sonnet 4.5 (baseline)
echo "LLM_PROVIDER=claude" >> .env
uv run medster-agent
# Run query, record metrics

# Test 2: GPT-5.1 (fast mode)
echo "LLM_PROVIDER=openai" >> .env
echo "REASONING_EFFORT=none" >> .env
uv run medster-agent
# Run query, record metrics

# Test 3: GPT-5.1 (deep reasoning)
echo "REASONING_EFFORT=high" >> .env
uv run medster-agent
# Run query, record metrics
```

---

## Troubleshooting

### Error: "No module named 'langchain_openai'"

**Solution**: Install dependencies
```bash
uv sync
```

### Error: "Invalid API key"

**Solution**: Verify your OpenAI API key
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Test key directly
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-proj-your-key-here"
```

### Error: "Model 'gpt-5.1' not found"

**Possible causes**:
1. GPT-5.1 not available in your region
2. API key doesn't have access to GPT-5.1
3. Model name typo

**Solution**: Use GPT-5 or GPT-4o instead
```bash
LLM_MODEL=gpt-5  # or gpt-4o
```

### Warning: Vision analysis not working with GPT-4o

**Check**: GPT-4o requires vision-enabled API access
```bash
# Verify model supports vision
# GPT-4o, GPT-4-turbo, GPT-5.1 all support vision
```

---

## Best Practices

### 1. Start with `reasoning.effort=none`

Default is fast and works well for most clinical queries:
```bash
REASONING_EFFORT=none
```

### 2. Only increase reasoning for complex cases

If diagnosis is unclear after initial analysis:
```bash
REASONING_EFFORT=medium
```

### 3. Use Claude for complex vision analysis

Claude Sonnet 4.5 has proven excellent for ECG/DICOM analysis:
```bash
LLM_PROVIDER=claude
```

### 4. Use GPT-5.1 for steerability testing

GPT-5.1's reasoning control enables experiments:
```bash
LLM_PROVIDER=openai
REASONING_EFFORT=high  # Test deep reasoning mode
```

### 5. Monitor costs

Higher reasoning effort = more tokens = higher cost:
- `none`: Baseline cost
- `low`: ~1.5x cost
- `medium`: ~2-3x cost
- `high`: ~5-10x cost

---

## Environment Variables Reference

```bash
# LLM Provider Selection
LLM_PROVIDER=openai           # "openai" or "claude"
LLM_MODEL=gpt-5.1             # Model name

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...    # Required for OpenAI
REASONING_EFFORT=none         # none, low, medium, high

# Claude Configuration
ANTHROPIC_API_KEY=sk-ant-...  # Required for Claude

# Reasoning Mode (separate from reasoning.effort)
REASONING_MODE=deterministic  # "deterministic" or "bayesian"
```

---

## Architecture

The dual-provider architecture uses a dispatcher pattern:

```python
def call_llm(prompt, model=None, ...):
    # Auto-detect from env if model not specified
    if model is None:
        provider = os.getenv("LLM_PROVIDER", "claude")
        if provider == "openai":
            model = os.getenv("LLM_MODEL", "gpt-5.1")
        else:
            model = os.getenv("LLM_MODEL", "claude-sonnet-4.5")

    # Route to appropriate provider
    if model.startswith("gpt") or model.startswith("o1"):
        return _call_openai(prompt, model, ...)
    else:
        return _call_claude(prompt, model, ...)
```

Both `_call_openai()` and `_call_claude()` support:
- ✅ Structured output (Pydantic schemas)
- ✅ Tool binding
- ✅ Vision analysis (multimodal)
- ✅ Retry logic with exponential backoff

---

## Future Enhancements

### Planned Features

1. **Dynamic reasoning effort** - Adjust based on query complexity
2. **Model ensembling** - Use both Claude and GPT for cross-validation
3. **Cost tracking** - Monitor token usage per provider
4. **A/B testing framework** - Compare clinical performance systematically
5. **Hybrid mode** - Claude for vision, GPT for reasoning

### Research Questions

- Does GPT-5.1 with `reasoning.effort=high` outperform Claude for complex differential diagnosis?
- Can we dynamically adjust reasoning effort based on validation confidence?
- What's the optimal reasoning effort for each clinical task type?
- Does GPT-5.1 handle medical code generation better than Claude?

---

## Summary

**Quick Comparison**:

| Use Case | Recommended Model | Settings |
|----------|------------------|----------|
| **General clinical analysis** | Claude Sonnet 4.5 | Default |
| **Fast data retrieval** | GPT-5.1 | `reasoning.effort=none` |
| **Complex reasoning** | GPT-5.1 | `reasoning.effort=high` |
| **Vision analysis (ECG/DICOM)** | Claude Sonnet 4.5 | Default |
| **Code generation** | GPT-5.1 | `reasoning.effort=none` |
| **Research/experimentation** | GPT-5.1 | `reasoning.effort=medium` |

**Default Configuration** (Recommended):
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.1
REASONING_EFFORT=none
REASONING_MODE=deterministic
```

This matches the speed and simplicity of the simplified deterministic mode while enabling GPT-5.1's steerability features for future experiments.
