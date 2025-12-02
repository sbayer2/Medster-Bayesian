# LLM Configuration

## Dual-Model Architecture

MDB supports **dual-model configuration** for optimal performance:

- **Primary LLM** (`LLM_MODEL`): Agent orchestration, planning, tool selection
- **Vision Model** (`VISION_MODEL`): Image analysis (DICOM, ECG, X-ray)

### Supported Providers

**OpenAI:**
- `gpt-4.1` - Primary orchestration model (recommended)
- `gpt-5.1` - Advanced reasoning with configurable effort
- `gpt-5` - GPT-5 base model

**Anthropic (Claude):**
- `claude-sonnet-4.5` (default) - Maps to `claude-sonnet-4-20250514`
- `claude-opus-4.5` - Maps to `claude-opus-4-5-20251101`
- `claude-haiku-4` - Maps to `claude-haiku-4-20250615`

## Configuration (.env)

```bash
# Choose provider
LLM_PROVIDER=openai  # or "claude"

# Primary model for agent loop
LLM_MODEL=gpt-4.1

# Vision model for image analysis
# Options:
#   - "claude-sonnet-4.5" (recommended for superior vision)
#   - "gpt-4.1" (for single-provider setup)
#   - "auto" (use same as LLM_MODEL)
VISION_MODEL=claude-sonnet-4.5

# GPT-5.1 Reasoning Effort (only for GPT-5.1/GPT-5)
# Options: none, low, medium, high
REASONING_EFFORT=none

# API Keys
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Model Selection Functions

**config.py:**
```python
get_primary_model() -> str
    # Returns primary LLM model for agent loop
    # Auto-detects based on LLM_PROVIDER if not set

get_vision_model() -> str
    # Returns vision model for image analysis
    # Defaults to claude-sonnet-4.5 (superior vision)
    # Set VISION_MODEL=auto to use same as primary
```

## Model Routing (model.py)

The `call_llm()` function routes to appropriate provider:

```python
call_llm(prompt, model=None, images=None, ...)
    ↓
# Auto-detect model from env if not specified
if model is None:
    model = get_primary_model()
    ↓
# Route based on model name
if model.startswith("gpt") or model.startswith("o1"):
    _call_openai(...)  # OpenAI format
else:
    _call_claude(...)  # Anthropic format
```

### Image Format Differences

**OpenAI:**
```python
{
    "type": "image_url",
    "image_url": {"url": "data:image/png;base64,{data}"}
}
```

**Claude:**
```python
{
    "type": "image",
    "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": data
    }
}
```

## Vision Analysis

Despite the misleading function name, `analyze_image_with_claude()` is **model-agnostic**:

```python
# primitives.py
def analyze_image_with_claude(image_base64: str, prompt: str) -> str:
    from medster.config import get_vision_model

    response = call_llm(
        prompt=prompt,
        images=[image_base64],
        model=get_vision_model()  # Routes to configured vision model!
    )
```

## Retry Logic

Both providers implement retry logic with exponential backoff:
- 3 attempts maximum
- Delays: 0.5s → 1s
- Handles transient connection errors
