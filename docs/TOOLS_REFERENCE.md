# Tools Reference

Complete reference for all MDB tools available to the agent.

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
- Uses sandboxed primitives from `primitives.py`
- Required: Code must define `analyze()` function returning dict
- Safety: Restricted globals (no file I/O, no imports, limited builtins)

**Vision Primitives** (`primitives.py`):

```python
# Patient Image Discovery
find_patient_images(patient_id: str) -> Dict
    # Returns: {"dicom_files": List[str], "dicom_count": int, "has_ecg": bool}

# DICOM Loading
load_dicom_image(patient_id: str, image_index: int = 0) -> Optional[str]
    # Returns base64 PNG string optimized for vision API
    # Automatically resizes from 32MB DICOM to ~200KB PNG

get_dicom_metadata(patient_id: str, image_index: int = 0) -> Dict
    # Returns: {"modality", "study_description", "body_part", "dimensions", ...}

# Fast DICOM Discovery (NEW - Fixed Patient ID Extraction)
scan_dicom_directory() -> List[str]
    # Scan entire DICOM directory, returns ALL file paths

extract_patient_id_from_dicom_path(dicom_path: str) -> str
    # Extract patient ID from DICOM filename path
    # Coherent format: FirstName_LastName_UUID[DICOM_ID].dcm
    # Returns: "FirstName_LastName" (e.g., "Abe604_Frami345")

get_dicom_metadata_from_path(dicom_path: str) -> Dict
    # Get metadata for DICOM file from file path

# ECG Loading
load_ecg_image(patient_id: str) -> Optional[str]
    # Returns base64 PNG from observations.csv

analyze_ecg_for_rhythm(patient_id: str, clinical_context: str = "") -> Dict
    # RECOMMENDED for ECG rhythm analysis - prevents false positives
    # Loads ECG, performs vision analysis, parses into structured data
    # Returns: {"patient_id", "ecg_available", "rhythm", "afib_detected",
    #           "rr_intervals", "p_waves", "baseline", "confidence",
    #           "clinical_significance", "raw_analysis"}

# Vision Analysis (Model-Agnostic)
analyze_image_with_claude(image_base64: str, prompt: str) -> str
    # Analyze single medical image using configured vision model
    # Routes to VISION_MODEL from .env (Claude or GPT-4.1)

analyze_multiple_images_with_claude(images: List[str], prompt: str) -> str
    # Analyze multiple images together
```

## Tool Registration

All tools must be added to `TOOLS` list in `tools/__init__.py` to be available to the agent.

## Sandbox Environment (code_generator.py)

Generated code executes in restricted sandbox with:

**Allowed:**
- FHIR primitives (get_patients, load_patient, get_conditions, etc.)
- Vision primitives (all functions listed above)
- Safe builtins (len, str, int, float, list, dict, etc.)
- Standard library: datetime, Counter, defaultdict
- Helper functions: log_progress, extract_patient_id_from_dicom_path

**Blocked:**
- File I/O operations
- Import statements (`__import__` not available)
- Dangerous builtins (eval, exec, compile, etc.)
- Network operations

## Key Implementation Patterns

### Task Decomposition for Batch Analysis

**IMPORTANT:** For batch/population queries, create a SINGLE task, not separate "list patients" + "analyze" tasks.

**Example:**
```
Query: "Analyze 100 patients for diabetes prevalence"
✅ Good: Task 1: "Analyze 100 patients for diabetes using analyze_batch_conditions"
❌ Bad: Task 1: "List 100 patients" → Task 2: "Analyze for diabetes"
```

### MCP Task Detection

Agent detects MCP-required tasks via keyword matching:
- Keywords: "mcp server", "mcp", "analyze_medical_document", "submit to mcp", "send to mcp"
- When detected AND tool not yet called, adds explicit reminder
- Tool must extract note text from previous outputs

### Argument Optimization

Agent calls `optimize_tool_args` before executing tools to:
- Fill in missing parameters based on task context
- Add filtering parameters to narrow results
- Improve data retrieval precision

Uses primary LLM model for all optimization tasks.

### Session Output Accumulation

All tool outputs are accumulated in `task_outputs` list and passed to subsequent LLM calls. This enables:
- Cross-task data sharing
- Meta-validation based on complete session history
- Comprehensive final analysis
