from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    UNSUPPORTED_MODALITY = "UNSUPPORTED_MODALITY"
    MISSING_METADATA = "MISSING_METADATA"
    PAIR_VALIDATION_FAILURE = "PAIR_VALIDATION_FAILURE"
    ALIGNMENT_FAILURE = "ALIGNMENT_FAILURE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    MODEL_EXECUTION_FAILURE = "MODEL_EXECUTION_FAILURE"
    TOOL_NOT_FOUND = "TOOL_NOT_FOUND"
    TOOL_EXECUTION_FAILURE = "TOOL_EXECUTION_FAILURE"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    EVIDENCE_GENERATION_FAILURE = "EVIDENCE_GENERATION_FAILURE"
    REPORT_GENERATION_FAILURE = "REPORT_GENERATION_FAILURE"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_SCHEMA_MISMATCH = "DATABASE_SCHEMA_MISMATCH"
    MODEL_REGISTRY_UNAVAILABLE = "MODEL_REGISTRY_UNAVAILABLE"
    IMAGE_OBJECT_MISSING = "IMAGE_OBJECT_MISSING"
    GROUNDING_POSTPROCESS_UNSUPPORTED = "GROUNDING_POSTPROCESS_UNSUPPORTED"


class ErrorPayload(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable explanation of failure")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured diagnostics or offending fields")
    trace_id: Optional[str] = Field(None, description="Request or execution correlation identifier")


class StandardErrorResponse(BaseModel):
    error: ErrorPayload


class ErrorResponse(BaseModel):
    """Backward-compatible error response schema."""
    detail: str
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    error: Optional[ErrorPayload] = None


class HealthResponse(BaseModel):
    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    version: str = Field(default="0.1.0")
    database: Optional[str] = Field(default="not_checked")
    storage: Optional[str] = Field(default="not_checked")


class ReadyResponse(BaseModel):
    status: str = Field(default="ready", description="Overall service readiness")
    version: str = Field(default="0.1.0")
    environment: str = Field(default="production")
    services: Dict[str, str] = Field(
        default_factory=dict,
        description="Individual service readiness statuses (database, storage, models, gpu)"
    )
