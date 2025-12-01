from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Task(BaseModel):
    """Represents a single task in a task list."""
    id: int = Field(..., description="Unique identifier for the task.")
    description: str = Field(..., description="The description of the task.")
    done: bool = Field(False, description="Whether the task is completed.")


class TaskList(BaseModel):
    """Represents a list of tasks."""
    tasks: List[Task] = Field(..., description="The list of tasks.")


class IsDone(BaseModel):
    """Represents the boolean status of a task."""
    done: bool = Field(..., description="Whether the task is done or not.")


class ValidationResult(BaseModel):
    """Represents the validation result with confidence and refinement suggestions."""
    done: bool = Field(..., description="Whether the task is completed.")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) in task completion.")
    data_completeness: float = Field(..., description="Data completeness score (0.0-1.0).")
    uncertainty_factors: List[str] = Field(default_factory=list, description="List of uncertainty factors or missing data.")
    refinement_suggestion: Optional[str] = Field(None, description="Suggestion for improving results if confidence is low.")


class BayesianMetaValidation(BaseModel):
    """Represents Bayesian meta-validation with confidence and uncertainty quantification."""
    achieved: bool = Field(..., description="Whether the overall clinical goal is achieved.")
    confidence: float = Field(..., description="Confidence score (0.0-1.0) that the goal is achieved.")
    remaining_uncertainty: float = Field(..., description="Remaining diagnostic uncertainty in bits.")
    missing_information: List[str] = Field(default_factory=list, description="List of missing information that would improve confidence.")


class Answer(BaseModel):
    """Represents an answer to the user's clinical query."""
    answer: str = Field(..., description="A comprehensive clinical analysis including relevant values, findings, temporal context, and clinical implications.")


class OptimizedToolArgs(BaseModel):
    """Represents optimized arguments for a tool call."""
    arguments: Dict[str, Any] = Field(..., description="The optimized arguments dictionary for the tool call.")


# Medical-specific schemas for future use

class CriticalValue(BaseModel):
    """Represents a critical lab or vital value requiring immediate attention."""
    parameter: str = Field(..., description="The parameter name (e.g., 'Potassium', 'Troponin')")
    value: float = Field(..., description="The measured value")
    unit: str = Field(..., description="Unit of measurement")
    reference_range: str = Field(..., description="Normal reference range")
    severity: str = Field(..., description="Severity level: critical, high, low")


class Medication(BaseModel):
    """Represents a medication entry."""
    name: str = Field(..., description="Medication name")
    dose: str = Field(..., description="Dosage")
    frequency: str = Field(..., description="Administration frequency")
    route: str = Field(..., description="Route of administration")
    start_date: Optional[str] = Field(None, description="Start date")
    indication: Optional[str] = Field(None, description="Clinical indication")


class LabResult(BaseModel):
    """Represents a laboratory result."""
    test_name: str = Field(..., description="Name of the lab test")
    value: str = Field(..., description="Result value")
    unit: str = Field(..., description="Unit of measurement")
    reference_range: str = Field(..., description="Reference range")
    status: str = Field(..., description="normal, high, low, critical")
    timestamp: str = Field(..., description="Collection timestamp")


class VitalSign(BaseModel):
    """Represents a vital sign measurement."""
    type: str = Field(..., description="Vital type: BP, HR, RR, Temp, SpO2")
    value: str = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement")
    timestamp: str = Field(..., description="Measurement timestamp")
