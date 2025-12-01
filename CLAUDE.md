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

## Core Architecture (Inherited from Medster)

MDB preserves Medster's autonomous clinical case analysis agent built on the Dexter architecture. It performs deep clinical analysis through autonomous task planning, tool selection, and self-validation using SYNTHEA/FHIR data and optional MCP server integration for complex document analysis.

## Core Architecture

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
The agent passes ALL session outputs (`task_outputs + task_step_outputs`) to `ask_for_actions`, not just current task outputs. This is essential for cross-task data access (e.g., discharge summary from Task 1 used in Task 2 for MCP analysis).

**Adaptive Optimization (NEW):**
The agent now implements a two-phase data discovery pattern when results don't match expectations:

**Phase 1 - Data Structure Discovery:**
- Detects incomplete results (e.g., 0 patients found when data should exist)
- Generates exploratory code to discover actual data structure
- Samples DICOM metadata, FHIR field names, etc. instead of assuming standard formats
- Example: If searching for brain MRI returns 0 results, first sample DICOM files to discover actual Modality/BodyPart values

**Phase 2 - Adaptation:**
- Uses discovered structure to generate corrected code
- Matches against real data patterns, not textbook assumptions
- Retries analysis with adapted approach
- Example: After discovering Coherent DICOM uses Modality='OT' (not 'MR'), adapts code to match actual values

**Detection Triggers:**
- 0 results when query implies data exists
- Cross-referencing failures (diagnosis exists but associated data not found)
- Results that don't logically answer the original query
- Tool output contradicts known database facts (e.g., "no DICOM files" when 298 exist)

This prevents the agent from making rigid assumptions about data structure and enables systematic adaptation when initial attempts fail.

### LLM Module (model.py)

The `call_llm` function exclusively uses Claude (Anthropic) models:

- Default model: `claude-opus-4.5` (maps to `claude-opus-4-5-20251101`)
- Supported models: `claude-sonnet-4.5`, `claude-opus-4.5`, `claude-haiku-4`
- Supports structured output via Pydantic schemas
- Implements retry logic with exponential backoff (3 attempts, 0.5s → 1s delays)
- Tool binding for autonomous tool selection

### Context Management (utils/context_manager.py)

Prevents token overflow when analyzing large datasets (e.g., 500 patients).

**Key Functions:**
- `format_output_for_context(tool_name, args, result)` - Truncates and summarizes large tool outputs
- `manage_context_size(outputs)` - Manages total context by prioritizing recent outputs
- `summarize_list_result(result)` - Summarizes list results (keeps first 20 items + count)
- `get_context_stats(outputs)` - Reports token utilization stats

**Token Limits:**
- `MAX_OUTPUT_TOKENS = 50000` - Max tokens for accumulated outputs
- `MAX_SINGLE_OUTPUT_TOKENS = 10000` - Max tokens per tool output
- Estimates ~3.5 characters per token for medical text

**Truncation Strategy:**
- Large outputs: Keeps 40% from start, 40% from end, adds truncation notice
- Context overflow: Keeps most recent outputs, drops older ones
- List results: Keeps first 20 items, adds `_total_count` and `_truncated` flags

**Agent Integration:**
- `ask_for_actions()` uses `manage_context_size()` for `last_outputs` parameter
- `_generate_answer()` uses `manage_context_size()` for final summary
- Logs warnings when context utilization exceeds 80%

### Prompts System (prompts.py)

**Key prompts:**
- `PLANNING_SYSTEM_PROMPT` - Task decomposition logic; includes batch analysis guidelines (DO NOT decompose into "list patients" + "analyze")
- `ACTION_SYSTEM_PROMPT` - Tool selection logic; includes MCP task detection AND adaptive optimization pattern
- `VALIDATION_SYSTEM_PROMPT` - Single task completion check; includes incomplete results detection
- `META_VALIDATION_SYSTEM_PROMPT` - Overall goal achievement check

**Mandatory DICOM Two-Task Pattern in PLANNING_SYSTEM_PROMPT:**
For any query involving DICOM/MRI/CT/imaging analysis, the planner MUST decompose into TWO tasks:
1. **Task 1 - Data Structure Discovery**: Explore DICOM database to discover actual metadata structure
2. **Task 2 - Adapted Analysis**: Use discovered structure to filter and analyze images

This prevents the agent from making textbook assumptions about DICOM metadata (e.g., Modality='MR' for MRI).

**Adaptive Optimization in ACTION_SYSTEM_PROMPT:**
Guides the agent to:
1. Use `scan_dicom_directory()` for fast database-wide DICOM access (no patient iteration)
2. Sample metadata with `get_dicom_metadata_from_path()` to discover actual field values
3. Known Coherent Data Set quirks: Modality='OT' (not 'MR'/'CT'), BodyPartExamined='Unknown'
4. Adapt filtering logic using discovered values, not assumed standards

**Enhanced Validation in VALIDATION_SYSTEM_PROMPT:**
Now detects incomplete results:
- Returns `{"done": false}` when 0 results on FIRST attempt without data exploration
- Checks if results logically answer the query
- Requires data structure exploration before accepting "data not available"
- Returns `{"done": true}` only after adaptation attempts or confirmed data absence

## Data Sources

### Coherent Data Set

Medster uses the **Coherent Data Set** (9 GB synthetic dataset):
- FHIR bundles (1,278 longitudinal patient records)
- DICOM imaging
- Genomic data
- Physiological data (ECGs)
- Clinical notes

**Location:** `./coherent_data/fhir/` (configured via `COHERENT_DATA_PATH` env var)
**Download:** https://synthea.mitre.org/downloads

**Data Access Pattern:**
- Patient bundles stored as individual JSON files
- `load_patient_bundle(patient_id)` loads from disk with caching
- All tools in `tools/medical/` parse FHIR resources directly

### MCP Server Integration

Medster connects to a FastMCP medical analysis server for specialist-level clinical reasoning:

**Recursive AI Architecture:**
- Local: Claude Sonnet 4.5 (Medster) - Orchestration, data extraction
- Remote: Claude Sonnet 4.5 (MCP Server) - Specialist medical document analysis

**Tool:** `analyze_medical_document` in `tools/analysis/mcp_client.py`

**Analysis Types:**
- `basic` - Quick extraction
- `comprehensive` - Detailed multi-step reasoning (default on server)
- `complicated` - Client-side alias for comprehensive (auto-mapped)

**Protocol:** JSON-RPC 2.0 with SSE response format
**Endpoints Tried:** `/mcp`, `/rpc`, `/analyze` (with automatic fallback)
**Debug Logging:** Set `MCP_DEBUG=true` to enable logging to `mcp_debug.log`

## Multimodal Analysis Capabilities

Medster supports **vision-based analysis** of medical images from the Coherent Data Set using Claude's vision API.

### Multimodal Data Structure

**DICOM Images** (`./coherent_data/dicom/`):
- 298 brain MRI scans (~32MB each, ~9GB total)
- Naming pattern: `FirstName_LastName_UUID[DICOM_ID].dcm`
- Modalities: MRI, CT, X-ray
- Automatically optimized to ~800x800 PNG (~200KB) for token efficiency

**ECG Waveforms** (`./coherent_data/csv/observations.csv`):
- Base64-encoded PNG images (already optimized)
- LOINC code: 29303009 (Electrocardiographic procedure)
- Ready for vision analysis without conversion

**Genomic Data** (`./coherent_data/dna/`):
- 889 CSV files with SNP variants
- Includes CVD risk markers, pathogenic variants
- Future enhancement: genomic analysis primitives

### Vision Primitives (`tools/analysis/primitives.py`)

Available to generated code via `generate_and_run_analysis`:

```python
find_patient_images(patient_id: str) -> Dict
    # Returns: {"dicom_files": List[str], "dicom_count": int, "has_ecg": bool}

load_dicom_image(patient_id: str, image_index: int = 0) -> Optional[str]
    # Returns base64 PNG string optimized for Claude vision API
    # Automatically resizes from 32MB DICOM to ~200KB PNG

load_ecg_image(patient_id: str) -> Optional[str]
    # Returns base64 PNG from observations.csv

get_dicom_metadata(patient_id: str, image_index: int = 0) -> Dict
    # Returns: {"modality", "study_description", "body_part", "dimensions", ...}

analyze_ecg_for_rhythm(patient_id: str, clinical_context: str = "") -> Dict
    # RECOMMENDED for ECG rhythm analysis - prevents false positives
    # Loads ECG, performs vision analysis, parses into structured data
    # Returns: {"patient_id", "ecg_available", "rhythm", "afib_detected",
    #           "rr_intervals", "p_waves", "baseline", "confidence",
    #           "clinical_significance", "raw_analysis"}
    # afib_detected: bool (based on RHYTHM field parsing, not keyword matching)
```

### Vision Analysis Workflow

**Two-step process for imaging analysis:**

1. **Generate code to load images** (using `generate_and_run_analysis`):
   ```python
   def analyze():
       patients = get_patients(10)
       imaging_data = []
       for pid in patients:
           images = find_patient_images(pid)
           if images["dicom_count"] > 0:
               img_base64 = load_dicom_image(pid, 0)
               metadata = get_dicom_metadata(pid, 0)
               imaging_data.append({
                   "patient": pid,
                   "modality": metadata["modality"],
                   "image": img_base64
               })
       return {"imaging_results": imaging_data}
   ```

2. **Agent analyzes images** (using `call_llm` with `images` parameter):
   - Agent extracts base64 images from code generation result
   - Calls `call_llm(prompt, images=[img1, img2, ...])` for vision analysis
   - Claude vision API analyzes imaging findings (masses, hemorrhage, fractures, etc.)

### Image Utilities (`utils/image_utils.py`)

**Token-efficient image conversion:**
- `dicom_to_base64_png()` - Converts DICOM → optimized PNG (32MB → ~200KB)
- `optimize_image()` - Resizes/compresses any image for API transmission
- `load_ecg_image_from_csv()` - Extracts ECG from observations CSV
- `find_patient_dicom_files()` - Locates all DICOM files for a patient

**Dependencies:**
- `pydicom` - DICOM file parsing and pixel data extraction
- `pillow` - Image optimization and format conversion

### Configuration

**Environment variables** (`.env`):
```bash
COHERENT_DICOM_PATH=./coherent_data/dicom
COHERENT_DNA_PATH=./coherent_data/dna
COHERENT_CSV_PATH=./coherent_data/csv
```

**Path management** (`config.py`):
- `COHERENT_DICOM_PATH_ABS` - Absolute path to DICOM directory
- `COHERENT_CSV_PATH_ABS` - Absolute path to CSV files (for ECG)
- `validate_paths()` - Checks all multimodal data directories exist

### Example Queries

**Vision-enabled clinical queries:**
- "Analyze stroke patients with brain MRI scans and identify imaging findings"
- "Review ECG waveforms for patients with atrial fibrillation"
- "Find patients with chest CT scans and correlate with respiratory conditions"
- "Analyze brain imaging for patients diagnosed with cerebrovascular accident"

**Note:** Vision analysis is only available through the `generate_and_run_analysis` tool with vision primitives. Direct image viewing tools are not implemented (follows token-efficient code generation pattern).

## Tool Categories

### Medical Data Tools (tools/medical/)

**Patient Data** (`patient_data.py`):
- `list_patients` - List available patient IDs from Coherent Data Set
- `get_patient_labs` - Laboratory results with reference ranges
- `get_vital_signs` - Vital sign measurements and trends
- `get_demographics` - Patient demographics
- `get_patient_conditions` - Diagnosis list
- `analyze_batch_conditions` - Batch condition prevalence analysis

**Clinical Notes** (`clinical_notes.py`):
- `get_clinical_notes` - Progress notes, H&Ps, consultations
- `get_soap_notes` - SOAP-formatted notes
- `get_discharge_summary` - Discharge summaries

**Medications** (`medications.py`):
- `get_medication_list` - Current and historical medications
- `check_drug_interactions` - Drug-drug interaction screening (simplified)

**Imaging** (`imaging.py`):
- `get_radiology_reports` - Imaging studies and interpretations

### Clinical Scoring (tools/clinical/)

**Scores** (`scores.py`):
- `calculate_clinical_score` - Wells' Criteria, CHA2DS2-VASc, CURB-65, MELD, etc.

### Analysis Tools (tools/analysis/)

**MCP Client** (`mcp_client.py`):
- `analyze_medical_document` - Delegates complex analysis to MCP server

**Code Generator** (`code_generator.py`):
- `generate_and_run_analysis` - Dynamic Python code execution for custom analysis
- Uses sandboxed primitives from `primitives.py` (get_patients, load_patient, get_conditions, etc.)
- Required: Code must define `analyze()` function returning dict
- Safety: Restricted globals (no file I/O, no imports, limited builtins)

## Development Commands

### Environment Setup

```bash
# Install dependencies
uv sync

# Or with pip
pip install -e .

# Setup environment
cp env.example .env
# Edit .env with API keys and paths
```

### Running the Agent

```bash
# Primary method (uses entry point)
uv run medster-agent

# Alternative
python -m medster.cli

# Direct execution
python src/medster/cli.py
```

### Development Tools

```bash
# Code formatting
black src/ --line-length 100

# Linting
ruff check src/

# Run with Anthropic API key
ANTHROPIC_API_KEY=xxx uv run medster-agent  # Uses Claude Sonnet 4.5
```

**Note:** No test suite currently implemented. The `tests/` directory referenced in `pyproject.toml` does not exist.

## Key Implementation Patterns

### Tool Registration

All tools must be added to `TOOLS` list in `tools/__init__.py` to be available to the agent.

### Task Decomposition for Batch Analysis

**IMPORTANT:** For batch/population queries (analyzing multiple patients), create a SINGLE task, not separate "list patients" + "analyze" tasks. Batch tools (`analyze_batch_conditions`, `generate_and_run_analysis`) fetch patients internally using `patient_limit` parameter.

**Example:**
```
Query: "Analyze 100 patients for diabetes prevalence"
Good: Task 1: "Analyze 100 patients for diabetes prevalence using analyze_batch_conditions"
Bad: Task 1: "List 100 patients" → Task 2: "Analyze for diabetes"
```

### MCP Task Detection

The agent detects MCP-required tasks via keyword matching in `ask_for_actions`:
- Keywords: "mcp server", "mcp", "analyze_medical_document", "submit to mcp", "send to mcp"
- When detected AND tool not yet called, adds explicit reminder to call `analyze_medical_document`
- Tool must extract note text from previous outputs (e.g., `result['discharge_summary']['text']`)

### Argument Optimization

The agent calls `optimize_tool_args` before executing tools to:
- Fill in missing parameters based on task context
- Add filtering parameters to narrow results
- Improve data retrieval precision

Uses `claude-sonnet-4.5` for all optimization tasks.

### Session Output Accumulation

All tool outputs are accumulated in `task_outputs` list and passed to subsequent LLM calls. This enables:
- Cross-task data sharing
- Meta-validation based on complete session history
- Comprehensive final analysis

## Environment Variables

Required in `.env` file:

```bash
# Required for Claude Sonnet 4.5
ANTHROPIC_API_KEY=sk-ant-...

# Required for Coherent Data Set access
COHERENT_DATA_PATH=./coherent_data/fhir

# Optional: MCP server for complex analysis
MCP_SERVER_URL=http://localhost:8000
MCP_API_KEY=...
MCP_DEBUG=true  # Enable debug logging
```

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
- Claude models: Must use official Anthropic model IDs
- Model mapping supports: `claude-sonnet-4.5`, `claude-opus-4`, `claude-haiku-4`
- Default model: `claude-sonnet-4.5` (recommended for clinical analysis)

### FHIR Data Access

All FHIR parsing happens in `tools/medical/api.py`:
- `load_patient_bundle` - Loads patient JSON files
- `extract_resources` - Filters bundle by resource type
- `format_*` functions - Convert FHIR resources to readable dicts

## Safety & Disclaimers

**IMPORTANT:** Medster is for research and educational purposes only.
- Not for clinical decision-making without physician review
- Critical value flagging is simplified (not comprehensive)
- Drug interaction checking is basic (not production-grade)
- Always verify findings with appropriate clinical resources

## Citation

When using the Coherent Data Set:

> Walonoski J, et al. The "Coherent Data Set": Combining Patient Data and Imaging in a Comprehensive, Synthetic Health Record. Electronics. 2022; 11(8):1199. https://doi.org/10.3390/electronics11081199

---

## Session Documentation (Read on Demand)

**Architecture & Analysis:**
- `docs/DEXTER_VS_MDB_ARCHITECTURE.md` - Comparison with original DEXTER architecture
- `docs/TOOL_ARCHITECTURE_ANALYSIS.md` - Tool sparsity principle and code generation
- `docs/MEDSTER_MENTAL_MODEL.md` - RockStar manager analogy (excellent for explaining to others)
- `docs/PLANNING_EVALUATION_ARCHITECTURE.md` - How planning actually works (one-shot, not algorithmic)

**Bayesian Mode Implementation:**
- `docs/BAYESIAN_MODE_GUIDE.md` - Quick start guide for Bayesian mode
- `docs/BAYESIAN_EFFICIENCY_ANALYSIS.md` - Deep dive into 2x efficiency gain sources
- `docs/BAYESIAN_PLANNING_IMPLEMENTATION.md` - Planning prompt enhancement details
- `docs/BAYESIAN_PROMPT_ANALYSIS.md` - Prompt comparison and optimization
- `docs/BAYESIAN_TEST_PROMPTS.md` - Test cases for meta-cognitive optimization
- `docs/BAYESIAN_TOGGLE_IMPLEMENTATION_SUMMARY.md` - Complete implementation summary
- `docs/TOGGLE_USAGE_GUIDE.md` - Detailed usage instructions

**Project History:**
- `docs/MIGRATION_SUMMARY.md` - Medster → MDB fork details
- `docs/README.md` - Original project README
- `docs/MCP_INTEGRATION_SUCCESS.md` - MCP server integration details
- `docs/MCP_DEBUGGING_SESSION_SUMMARY.md` - MCP debugging notes

**Usage:** Read these files on-demand when you need specific information about architecture, implementation details, or historical context. This keeps the main CLAUDE.md file focused on essential development guidance.