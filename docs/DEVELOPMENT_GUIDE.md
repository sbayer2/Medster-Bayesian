# Development Guide

## Environment Setup

```bash
# Install dependencies
uv sync

# Or with pip
pip install -e .

# Setup environment
cp env.example .env
# Edit .env with API keys and paths
```

## Running the Agent

```bash
# Primary method (uses entry point)
uv run medster-agent

# Alternative
python -m medster.cli

# Direct execution
python src/medster/cli.py
```

## Development Tools

```bash
# Code formatting
black src/ --line-length 100

# Linting
ruff check src/

# Run with specific API key
ANTHROPIC_API_KEY=xxx uv run medster-agent
OPENAI_API_KEY=xxx uv run medster-agent
```

**Note:** No test suite currently implemented. The `tests/` directory referenced in `pyproject.toml` does not exist.

## Code Modification Guidelines

### Adding New Tools

1. Create tool function with `@tool` decorator and Pydantic input schema
2. Import in `tools/__init__.py`
3. Add to `TOOLS` list
4. Update prompt descriptions in `prompts.py` (PLANNING_SYSTEM_PROMPT, ACTION_SYSTEM_PROMPT)

### Modifying Agent Loop

- Be cautious with step limits - prevent runaway loops
- Maintain output accumulation pattern (pass full history to LLM)
- Preserve loop detection logic (last 4 actions check)
- Always return structured data from tools (JSON/dict)

### Changing Models

Update model names in `model.py`:
- OpenAI models: `gpt-4.1`, `gpt-5.1`, `gpt-5`
- Claude models: Must use official Anthropic model IDs
- Model mapping supports: `claude-sonnet-4.5`, `claude-opus-4.5`, `claude-haiku-4`

See `docs/LLM_CONFIGURATION.md` for complete model configuration details.

### FHIR Data Access

All FHIR parsing happens in `tools/medical/api.py`:
- `load_patient_bundle` - Loads patient JSON files
- `extract_resources` - Filters bundle by resource type
- `format_*` functions - Convert FHIR resources to readable dicts

## Environment Variables

Required in `.env` file:

```bash
# LLM Configuration
LLM_PROVIDER=openai  # or "claude"
LLM_MODEL=gpt-4.1
VISION_MODEL=claude-sonnet-4.5

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...

# Required for Coherent Data Set access
COHERENT_DATA_PATH=/path/to/coherent_data/fhir
COHERENT_DICOM_PATH=/path/to/coherent_data/dicom
COHERENT_DNA_PATH=/path/to/coherent_data/dna
COHERENT_CSV_PATH=/path/to/coherent_data/csv

# Optional: MCP server for complex analysis
MCP_SERVER_URL=http://localhost:8000
MCP_API_KEY=...
MCP_DEBUG=true  # Enable debug logging

# Optional: Bayesian mode (experimental)
REASONING_MODE=deterministic  # or "bayesian"

# Optional: GPT-5.1 reasoning effort
REASONING_EFFORT=none  # none, low, medium, high
```

## Context Management

See `utils/context_manager.py` for token overflow prevention:

**Key Functions:**
- `format_output_for_context(tool_name, args, result)` - Truncates and summarizes large tool outputs
- `manage_context_size(outputs)` - Manages total context by prioritizing recent outputs
- `summarize_list_result(result)` - Summarizes list results (keeps first 20 items + count)
- `get_context_stats(outputs)` - Reports token utilization stats

**Token Limits:**
- `MAX_OUTPUT_TOKENS = 50000` - Max tokens for accumulated outputs
- `MAX_SINGLE_OUTPUT_TOKENS = 10000` - Max tokens per tool output
- Estimates ~3.5 characters per token for medical text

## Safety & Disclaimers

**IMPORTANT:** MDB is for research and educational purposes only.
- Not for clinical decision-making without physician review
- Critical value flagging is simplified (not comprehensive)
- Drug interaction checking is basic (not production-grade)
- Always verify findings with appropriate clinical resources

## Citation

When using the Coherent Data Set:

> Walonoski J, et al. The "Coherent Data Set": Combining Patient Data and Imaging in a Comprehensive, Synthetic Health Record. Electronics. 2022; 11(8):1199. https://doi.org/10.3390/electronics11081199
