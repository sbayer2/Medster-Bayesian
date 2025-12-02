# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MDB (Medster-Bayesian-Diagnostics)** is an experimental fork of Medster exploring Bayesian reasoning algorithms for clinical decision support.

**Parent Project**: [Medster](https://github.com/sbayer2/Medster) - Autonomous clinical case analysis agent

**Research Focus**: Integration of Bayesian inference methods (prior-posterior updating, likelihood ratios, uncertainty quantification) with Medster's proven multi-agent architecture.

**Key Differences from Medster**:
- Probabilistic differential diagnosis generation
- Explicit uncertainty quantification
- Information-theoretic test selection
- Bayesian risk stratification models
- Research-grade probability estimates (not clinically validated)

**Development Status**: Early-stage experimental development. Core Medster architecture preserved; Bayesian modules under active development.

**Data Sharing**: MDB shares the Coherent Data Set with Medster via absolute paths in `.env` to avoid 23GB duplication.

## Core Architecture

MDB preserves Medster's autonomous clinical case analysis agent built on the Dexter architecture. It performs deep clinical analysis through autonomous task planning, tool selection, and self-validation using SYNTHEA/FHIR data.

### Multi-Agent Loop (agent.py)

The agent implements a proven 4-phase execution loop:

1. **Planning Module** (`plan_tasks`) - Decomposes clinical queries into task sequences
2. **Action Module** (`ask_for_actions`) - Selects tools to execute based on task context
3. **Validation Module** (`ask_if_done`) - Verifies task completion
4. **Synthesis Module** (`_generate_answer`) - Generates comprehensive clinical analysis

**Safety Mechanisms:**
- Global step limit: 20 steps (configurable via `max_steps`)
- Per-task step limit: 5 steps (configurable via `max_steps_per_task`)
- Loop detection: Prevents repetitive tool calls (tracks last 4 actions)
- Tool execution tracking: All outputs accumulated in `task_outputs` list

**Critical Implementation Detail:**
The agent passes ALL session outputs (`task_outputs + task_step_outputs`) to `ask_for_actions`, not just current task outputs. This is essential for cross-task data access.

### Adaptive Optimization

The agent implements a two-phase data discovery pattern when results don't match expectations:

**Phase 1 - Data Structure Discovery:**
- Detects incomplete results (e.g., 0 patients found when data should exist)
- Generates exploratory code to discover actual data structure
- Samples DICOM metadata, FHIR field names, etc. instead of assuming standard formats

**Phase 2 - Adaptation:**
- Uses discovered structure to generate corrected code
- Matches against real data patterns, not textbook assumptions
- Retries analysis with adapted approach

**Detection Triggers:**
- 0 results when query implies data exists
- Cross-referencing failures
- Results that don't logically answer the original query
- Tool output contradicts known database facts

This prevents the agent from making rigid assumptions about data structure and enables systematic adaptation when initial attempts fail.

## LLM Configuration

MDB supports **dual-model architecture** for optimal performance:
- **Primary LLM** (`LLM_MODEL`): Agent orchestration - GPT-4.1 or Claude Sonnet 4.5
- **Vision Model** (`VISION_MODEL`): Image analysis - Claude Sonnet 4.5 (recommended) or GPT-4.1

**Key Functions** (config.py):
- `get_primary_model()` - Returns primary LLM for agent loop
- `get_vision_model()` - Returns vision model for image analysis

**Model Routing** (model.py):
- `call_llm()` - Routes to OpenAI or Claude based on model name
- Handles provider-specific image formats automatically
- Implements retry logic with exponential backoff

See `docs/LLM_CONFIGURATION.md` for complete configuration details.

## Prompts System (prompts.py)

**Key prompts:**
- `PLANNING_SYSTEM_PROMPT` - Task decomposition logic with batch analysis guidelines
- `ACTION_SYSTEM_PROMPT` - Tool selection logic with MCP detection and adaptive optimization
- `VALIDATION_SYSTEM_PROMPT` - Task completion check with incomplete results detection
- `META_VALIDATION_SYSTEM_PROMPT` - Overall goal achievement check

**Mandatory DICOM Two-Task Pattern:**
For any query involving DICOM/MRI/CT/imaging analysis, the planner MUST decompose into:
1. **Task 1 - Data Structure Discovery**: Explore DICOM database to discover actual metadata structure
2. **Task 2 - Adapted Analysis**: Use discovered structure to filter and analyze images

**Known Coherent Data Set Quirks:**
- DICOM Modality: `'OT'` (not standard `'MR'`/`'CT'`)
- BodyPartExamined: `'Unknown'` (not anatomical names)
- Filename format: `FirstName_LastName_UUID[DICOM_ID].dcm`

## Data Sources

### Coherent Data Set

9 GB synthetic medical dataset:
- FHIR bundles (1,278 longitudinal patient records)
- DICOM imaging (298 brain MRI scans, ~32MB each)
- Genomic data (889 CSV files with SNP variants)
- ECG waveforms (base64-encoded PNG images)
- Clinical notes

**Location:** Configured via environment variables in `.env`
**Download:** https://synthea.mitre.org/downloads

**Data Access:**
- Patient bundles: Individual JSON files loaded via `load_patient_bundle(patient_id)`
- DICOM images: Optimized to ~800x800 PNG (~200KB) for token efficiency
- ECG images: Pre-encoded base64 PNG ready for vision analysis

### MCP Server Integration (Optional)

Connects to FastMCP medical analysis server for specialist-level clinical reasoning:

**Tool:** `analyze_medical_document` in `tools/analysis/mcp_client.py`

**Analysis Types:**
- `basic` - Quick extraction
- `comprehensive` - Detailed multi-step reasoning (default on server)
- `complicated` - Client-side alias for comprehensive

**Protocol:** JSON-RPC 2.0 with SSE response format

## Multimodal Analysis

### Vision Primitives (tools/analysis/primitives.py)

Key functions for DICOM/ECG analysis:

```python
# Fast DICOM Discovery (RECOMMENDED)
scan_dicom_directory() -> List[str]
    # Returns ALL DICOM file paths instantly

extract_patient_id_from_dicom_path(dicom_path: str) -> str
    # Extract patient ID from filename
    # Format: FirstName_LastName_UUID[DICOM_ID].dcm
    # Returns: "FirstName_LastName"

get_dicom_metadata_from_path(dicom_path: str) -> Dict
    # Get metadata for DICOM file from path

# Patient-Specific Loading
load_dicom_image(patient_id: str, image_index: int = 0) -> Optional[str]
    # Returns base64 PNG optimized for vision API

load_ecg_image(patient_id: str) -> Optional[str]
    # Returns base64 PNG from observations.csv

# Vision Analysis (Model-Agnostic)
analyze_image_with_claude(image_base64: str, prompt: str) -> str
    # Routes to configured VISION_MODEL (Claude or GPT-4.1)
```

### Vision Analysis Workflow

**Two-step process:**
1. **Generate code to load images** via `generate_and_run_analysis`
2. **Agent analyzes images** via `call_llm(prompt, images=[...])` with vision model

**Note:** Despite the function name, `analyze_image_with_claude()` is model-agnostic and routes to the configured `VISION_MODEL`.

## Tools Overview

See `docs/TOOLS_REFERENCE.md` for complete tool documentation.

**Tool Categories:**
- **Medical Data**: Patient data, labs, vitals, conditions, medications
- **Clinical Notes**: SOAP notes, progress notes, discharge summaries
- **Clinical Scoring**: Wells' Criteria, CHA2DS2-VASc, CURB-65, MELD
- **Analysis**: MCP client, code generator, vision primitives
- **Imaging**: Radiology reports

**Key Tool:**
- `generate_and_run_analysis` - Dynamic Python code execution in sandboxed environment
- Code must define `analyze()` function returning dict
- Has access to all FHIR and vision primitives

## Development

See `docs/DEVELOPMENT_GUIDE.md` for complete development instructions.

**Quick Start:**
```bash
# Install
uv sync

# Setup .env with API keys
cp env.example .env

# Run
uv run medster-agent
```

**Environment Variables:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1
VISION_MODEL=claude-sonnet-4.5
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
COHERENT_DATA_PATH=/path/to/coherent_data/fhir
```

## Documentation Index

**Architecture & Implementation:**
- `docs/LLM_CONFIGURATION.md` - Dual-model architecture, provider routing, vision analysis
- `docs/TOOLS_REFERENCE.md` - Complete tool documentation and usage patterns
- `docs/DEVELOPMENT_GUIDE.md` - Setup, commands, modification guidelines
- `docs/DEXTER_VS_MDB_ARCHITECTURE.md` - Comparison with original DEXTER
- `docs/TOOL_ARCHITECTURE_ANALYSIS.md` - Tool sparsity principle
- `docs/MEDSTER_MENTAL_MODEL.md` - RockStar manager analogy

**Bayesian Mode (Experimental):**
- `docs/BAYESIAN_MODE_GUIDE.md` - Quick start guide
- `docs/BAYESIAN_EFFICIENCY_ANALYSIS.md` - 2x efficiency gain analysis
- `docs/BAYESIAN_PLANNING_IMPLEMENTATION.md` - Prompt enhancements
- `docs/TOGGLE_USAGE_GUIDE.md` - Usage instructions

**Project History:**
- `docs/MIGRATION_SUMMARY.md` - Medster → MDB fork details
- `docs/MCP_INTEGRATION_SUCCESS.md` - MCP server integration
- `docs/MCP_DEBUGGING_SESSION_SUMMARY.md` - MCP debugging notes

**Usage:** Read these files on-demand when you need specific information about architecture, implementation details, or historical context.

## Safety & Disclaimers

**IMPORTANT:** MDB is for research and educational purposes only.
- Not for clinical decision-making without physician review
- Critical value flagging is simplified (not comprehensive)
- Drug interaction checking is basic (not production-grade)
- Always verify findings with appropriate clinical resources
