"""
Pydantic Schemas for AI Analysis Services (VQA, Captioning, Job Tracking).
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VqaRequest(BaseModel):
    image_id: uuid.UUID = Field(..., description="Target satellite image identifier")
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language question about the image")


class VqaResponse(BaseModel):
    analysis_id: uuid.UUID
    status: str
    task: str = "visual_question_answering"
    answer: str
    confidence: float
    confidence_method: str
    model: str
    model_version: str
    processing_time_ms: int
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    is_adapted: bool = False
    adapter_metadata: Optional[Dict[str, Any]] = None
    fallback: Optional[Dict[str, Any]] = None


class CaptionRequest(BaseModel):
    image_id: uuid.UUID = Field(..., description="Target satellite image identifier")


class CaptionResponse(BaseModel):
    analysis_id: uuid.UUID
    status: str
    task: str = "image_captioning"
    caption: str
    confidence: float
    confidence_method: str
    model: str
    model_version: str
    processing_time_ms: int
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class AnalysisJobResponse(BaseModel):
    id: uuid.UUID
    image_id: uuid.UUID
    task: str
    query: Optional[str] = None
    model_name: str
    model_version: str
    status: str
    result_json: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None
    confidence_method: Optional[str] = None
    processing_time_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None


class ModelInfoSchema(BaseModel):
    name: str
    version: str
    task: str
    supported_modalities: List[str]
    is_default_for_task: bool
    is_adapted: Optional[bool] = False
    adapter_type: Optional[str] = None
    dataset_provenance: Optional[str] = None
    base_model: Optional[str] = None


class GroundingRequest(BaseModel):
    image_id: uuid.UUID = Field(..., description="Target satellite image identifier")
    query: str = Field(..., min_length=1, max_length=1000, description="Referring expression or target feature to locate")


class GroundingResponse(BaseModel):
    analysis_id: uuid.UUID
    status: str
    task: str = "grounding"
    answer: str
    confidence: float
    confidence_method: str
    model: str
    model_version: str
    processing_time_ms: int
    regions: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    artifact_key: Optional[str] = None


class EvidenceResponseSchema(BaseModel):
    id: uuid.UUID
    analysis_id: uuid.UUID
    image_id: uuid.UUID
    type: str
    label: str
    confidence: float
    geometry: Optional[Any] = None
    pixel_geometry: Dict[str, Any]
    geo_geometry: Optional[Dict[str, Any]] = None
    artifact_key: Optional[str] = None
    crop_artifact_key: Optional[str] = None
    created_at: datetime.datetime

