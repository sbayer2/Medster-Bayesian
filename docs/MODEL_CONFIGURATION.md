# Model Configuration Architecture

## Overview

MDB implements a flexible dual-model architecture that allows you to configure separate models for agent orchestration and vision analysis. This enables hybrid setups (e.g., GPT-4.1 for orchestration + Claude for vision) or pure single-provider configurations.

## Configuration (.env)

```bash
# Primary model for agent loop (planning, action, validation, answer)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1

# Vision model for image analysis (DICOM, ECG, X-ray)
VISION_MODEL=claude-sonnet-4.5  # Recommended: Claude for superior vision
# VISION_MODEL=auto             # Alternative: Use same model as LLM_MODEL

# Model-specific parameters
REASONING_EFFORT=none  # For GPT-5.1 only (none/low/medium/high)
```

## Model Selection Logic

### Primary Model (Agent Loop)

**What it controls:**
- Planning (task decomposition)
- Action selection (tool choice)
- Argument optimization (parameter filling)
- Validation (task completion checks)
- Answer generation (final synthesis)

**Configuration:**
```python
from medster.config import get_primary_model

# Returns LLM_MODEL from .env, or auto-detects from LLM_PROVIDER
model = get_primary_model()  # "gpt-4.1" or "claude-sonnet-4.5"
```

**Usage in code:**
```python
# Call LLM without model parameter - uses .env configuration
call_llm(prompt, system_prompt=..., output_schema=...)
```

### Vision Model (Image Analysis)

**What it controls:**
- DICOM image analysis (brain MRI, CT scans)
- ECG waveform interpretation
- X-ray analysis
- Multi-image comparison

**Configuration:**
```python
from medster.config import get_vision_model

# Returns VISION_MODEL from .env
# Defaults to "claude-sonnet-4.5" if not set
# Returns same as LLM_MODEL if VISION_MODEL=auto
model = get_vision_model()
```

**Usage in code:**
```python
# Vision analysis uses configured model
call_llm(prompt, images=[img1, img2], model=get_vision_model())
```

## Supported Configurations

### 1. Hybrid Architecture (RECOMMENDED)

**Setup:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1
VISION_MODEL=claude-sonnet-4.5
```

**Advantages:**
- GPT-4.1: Fast, cost-effective orchestration
- Claude: Superior vision analysis quality
- Best of both worlds

**Requirements:**
- Both OpenAI and Anthropic API keys

**Use case:**
Production deployments requiring high-quality vision analysis

---

### 2. Pure OpenAI

**Setup:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1
VISION_MODEL=auto
```

**Advantages:**
- Single API key required
- Simplified billing
- Still capable vision analysis

**Requirements:**
- OpenAI API key only

**Use case:**
Cost-sensitive deployments, or when Anthropic API not available

---

### 3. Pure Claude

**Setup:**
```bash
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-4.5
VISION_MODEL=auto
```

**Advantages:**
- Single API key required
- Excellent vision quality
- Strong reasoning capabilities

**Requirements:**
- Anthropic API key only

**Use case:**
Teams already standardized on Anthropic

---

### 4. GPT-5.1 Reasoning (Experimental)

**Setup:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-5.1
REASONING_EFFORT=medium
VISION_MODEL=claude-sonnet-4.5
```

**Advantages:**
- Advanced reasoning for complex cases
- Configurable reasoning depth

**Disadvantages:**
- Tool calling issues with `/v1/responses` endpoint
- Not recommended for production (use GPT-4.1 instead)

**Requirements:**
- OpenAI API key with GPT-5.1 access

**Use case:**
Experimental research only

---

## Model-Specific Parameters

### GPT-5.1 Reasoning Effort

Only applies to `gpt-5.1` and `gpt-5` models.

```bash
REASONING_EFFORT=none   # Fastest (default)
REASONING_EFFORT=low    # Light reasoning
REASONING_EFFORT=medium # Balanced
REASONING_EFFORT=high   # Most thorough
```

**Note:** GPT-4.1 and Claude ignore this parameter.

### Temperature

Hardcoded to `0` for all models (deterministic medical analysis).

## Code Architecture

### config.py

Central configuration module:

```python
def get_primary_model() -> str:
    """Returns LLM_MODEL from .env or auto-detects default"""
    if LLM_MODEL:
        return LLM_MODEL
    return "gpt-4.1" if LLM_PROVIDER == "openai" else "claude-sonnet-4.5"

def get_vision_model() -> str:
    """Returns VISION_MODEL from .env (defaults to Claude)"""
    if VISION_MODEL == "auto":
        return get_primary_model()
    return VISION_MODEL  # Default: "claude-sonnet-4.5"
```

### model.py

LLM dispatcher with auto-detection:

```python
def call_llm(
    prompt: str,
    model: str = None,  # Auto-detect from .env if not specified
    reasoning_effort: str = "none",
    ...
):
    # Auto-detect model from .env
    if model is None:
        model = get_primary_model()

    # Route to appropriate provider
    if model.startswith("gpt") or model.startswith("o1"):
        return _call_openai(...)
    else:
        return _call_claude(...)
```

### agent.py

Agent loop uses auto-detection:

```python
# Planning
tasks = call_llm(prompt, system_prompt=PLANNING_PROMPT, ...)

# Action selection
actions = call_llm(prompt, system_prompt=ACTION_PROMPT, tools=TOOLS)

# Argument optimization (FIXED - was hardcoded to Claude)
optimized = call_llm(prompt, system_prompt=TOOL_ARGS_PROMPT, ...)

# Validation
is_done = call_llm(prompt, system_prompt=VALIDATION_PROMPT, ...)
```

### Vision Analysis

All vision functions use configured model:

```python
# primitives.py
def analyze_image_with_claude(image_base64, prompt):
    from medster.config import get_vision_model
    return call_llm(prompt, images=[image_base64], model=get_vision_model())

# vision_analyzer.py
def analyze_medical_images(image_paths, prompt):
    from medster.config import get_vision_model
    return call_llm(prompt, images=imgs, model=get_vision_model())
```

## Troubleshooting

### Issue: "patient_limit validation error"

**Cause:** Argument optimizer returns `None` for optional parameters

**Fix:** Applied in commit `6d16688` - filters out None values

```python
# Filter None values to allow tool defaults
filtered_args = {k: v for k, v in args.items() if v is not None}
```

### Issue: Wrong model being used

**Diagnosis:**
```python
# Check what's configured
from medster.config import get_primary_model, get_vision_model
print(f"Primary: {get_primary_model()}")
print(f"Vision: {get_vision_model()}")
```

**Check .env:**
```bash
echo $LLM_MODEL
echo $VISION_MODEL
```

### Issue: GPT-5.1 tool calling fails

**Symptom:** Tasks marked complete but no data retrieved

**Cause:** GPT-5.1 reasoning API incompatible with LangChain tool binding

**Solution:** Use GPT-4.1 instead:
```bash
LLM_MODEL=gpt-4.1  # Not gpt-5.1
```

## Migration Guide

### From Hardcoded Models

**Before (commit < 6d16688):**
```python
# Hardcoded in agent.py
call_llm(prompt, model="claude-sonnet-4.5", ...)

# Hardcoded in primitives.py
call_llm(prompt, images=[img], model="claude-sonnet-4.5")
```

**After (commit >= 6d16688):**
```python
# Respects .env configuration
call_llm(prompt, ...)  # Uses get_primary_model()

# Vision uses configured model
from medster.config import get_vision_model
call_llm(prompt, images=[img], model=get_vision_model())
```

### From Claude to GPT-4.1

1. Update `.env`:
   ```bash
   LLM_PROVIDER=openai
   LLM_MODEL=gpt-4.1
   VISION_MODEL=claude-sonnet-4.5  # Keep Claude for vision (hybrid)
   ```

2. Add OpenAI API key:
   ```bash
   OPENAI_API_KEY=sk-proj-...
   ```

3. Test:
   ```bash
   uv run medster-agent
   # Check banner shows "GPT-4.1"
   ```

### From Single Provider to Hybrid

1. Add second API key:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...  # If using Claude vision
   OPENAI_API_KEY=sk-proj-...    # If using GPT orchestration
   ```

2. Configure models:
   ```bash
   LLM_MODEL=gpt-4.1
   VISION_MODEL=claude-sonnet-4.5
   ```

## Performance Comparison

| Configuration | Agent Speed | Vision Quality | Cost | API Keys |
|--------------|-------------|----------------|------|----------|
| Hybrid (GPT-4.1 + Claude) | Fast | Excellent | Medium | 2 |
| Pure GPT-4.1 | Fast | Good | Low | 1 |
| Pure Claude | Medium | Excellent | Medium | 1 |
| GPT-5.1 + Claude | Slow | Excellent | High | 2 |

**Recommendation:** Hybrid (GPT-4.1 orchestration + Claude vision) for production

## Testing

Test your configuration:

```bash
# Test primary model
uv run medster-agent
# Query: "List 5 patients"
# Check logs show correct model API calls

# Test vision model
# Query: "Analyze brain MRI for patient with stroke"
# Check logs show vision model API calls
```

Expected logs:
```
HTTP Request: POST https://api.openai.com/v1/chat/completions      # Agent loop
HTTP Request: POST https://api.anthropic.com/v1/messages           # Vision (if using Claude)
```

## Best Practices

1. **Use hybrid architecture** for production (GPT-4.1 + Claude vision)
2. **Set VISION_MODEL explicitly** in .env (don't rely on defaults)
3. **Never hardcode models** in code - always use config helpers
4. **Test both models** after configuration changes
5. **Document your setup** in deployment notes

## Related Documentation

- `GPT_5.1_INTEGRATION.md` - GPT-5.1 specific features and issues
- `SIMPLIFIED_ARCHITECTURE.md` - Agent refinement architecture
- `CLAUDE.md` - Complete project documentation
