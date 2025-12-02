"""
Configuration module for Medster.

Loads environment variables and provides centralized access to configuration values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Coherent Data Set paths
COHERENT_FHIR_PATH = os.getenv("COHERENT_DATA_PATH", "./coherent_data/fhir")
COHERENT_DICOM_PATH = os.getenv("COHERENT_DICOM_PATH", "./coherent_data/dicom")
COHERENT_DNA_PATH = os.getenv("COHERENT_DNA_PATH", "./coherent_data/dna")
COHERENT_CSV_PATH = os.getenv("COHERENT_CSV_PATH", "./coherent_data/csv")

# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
MCP_API_KEY = os.getenv("MCP_API_KEY")
MCP_DEBUG = os.getenv("MCP_DEBUG", "false").lower() == "true"

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# MDB-Bayesian Configuration
# Set to "bayesian" for probabilistic reasoning, "deterministic" for original Medster
REASONING_MODE = os.getenv("REASONING_MODE", "deterministic").lower()

# LLM Model Configuration
# Primary model for agent loop (planning, action, validation, answer)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()
LLM_MODEL = os.getenv("LLM_MODEL")  # None = auto-detect in call_llm
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "none")  # For GPT-5.1 only

# Vision model for image analysis (defaults to Claude for superior vision capabilities)
# Set to "auto" to use same model as LLM_MODEL, or specify a model explicitly
VISION_MODEL = os.getenv("VISION_MODEL", "claude-sonnet-4.5")


def get_primary_model() -> str:
    """
    Get the primary LLM model for agent loop operations.

    Returns:
        Model name (e.g., "gpt-4.1", "claude-sonnet-4.5")
        Returns None to trigger auto-detection in call_llm()
    """
    if LLM_MODEL:
        return LLM_MODEL

    # Auto-detect default based on provider
    if LLM_PROVIDER == "openai":
        return "gpt-4.1"
    else:
        return "claude-sonnet-4.5"


def get_vision_model() -> str:
    """
    Get the vision model for image analysis.

    Returns:
        Model name for vision analysis
        Defaults to Claude Sonnet 4.5 (superior vision capabilities)
        Set VISION_MODEL=auto in .env to use same as primary model
    """
    if VISION_MODEL == "auto":
        return get_primary_model()
    return VISION_MODEL


def get_absolute_path(relative_path: str) -> Path:
    """
    Convert relative path to absolute path.

    Args:
        relative_path: Relative path string

    Returns:
        Absolute Path object
    """
    if os.path.isabs(relative_path):
        return Path(relative_path)

    # Use current working directory as base for relative paths
    # This ensures paths resolve correctly when running from project directory
    # regardless of where the package is installed
    return (Path(os.getcwd()) / relative_path).resolve()


# Convert all Coherent Data paths to absolute paths
COHERENT_FHIR_PATH_ABS = get_absolute_path(COHERENT_FHIR_PATH)
COHERENT_DICOM_PATH_ABS = get_absolute_path(COHERENT_DICOM_PATH)
COHERENT_DNA_PATH_ABS = get_absolute_path(COHERENT_DNA_PATH)
COHERENT_CSV_PATH_ABS = get_absolute_path(COHERENT_CSV_PATH)


def validate_paths():
    """
    Validate that all required data paths exist.

    Raises:
        FileNotFoundError: If required paths don't exist
    """
    paths_to_check = [
        ("FHIR", COHERENT_FHIR_PATH_ABS),
        ("DICOM", COHERENT_DICOM_PATH_ABS),
        ("DNA", COHERENT_DNA_PATH_ABS),
        ("CSV", COHERENT_CSV_PATH_ABS),
    ]

    missing_paths = []
    for name, path in paths_to_check:
        if not path.exists():
            missing_paths.append(f"{name}: {path}")

    if missing_paths:
        raise FileNotFoundError(
            f"Required Coherent Data Set paths not found:\n" +
            "\n".join(f"  - {p}" for p in missing_paths) +
            "\n\nPlease check your .env configuration and ensure the Coherent Data Set is extracted."
        )
