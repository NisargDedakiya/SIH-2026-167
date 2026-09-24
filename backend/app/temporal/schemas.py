"""
Pydantic Schemas for Bi-Temporal Change Intelligence.
Defines strict API contracts for pair validation, change analysis, and region extraction.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BiTemporalPairCreate(BaseModel):
    image_t1_id: uuid.UUID = Field(..., description="UUID of earlier satellite image (T1)")
    image_t2_id: uuid.UUID = Field(..., description="UUID of later satellite image (T2)")
    acquisition_time_t1: Optional[datetime.datetime] = Field(
        None, description="Optional override/explicit acquisition timestamp for T1"
    )
    acquisition_time_t2: Optional[datetime.datetime] = Field(
        None, description="Optional override/explicit acquisition timestamp for T2"
    )


class PairValidationResult(BaseModel):
    valid: bool
    temporal_valid: bool
    spatially_compatible: bool
    overlap_ratio: float = 0.0
    status_code: str = "VALID"
    message: str
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class PairImageSummary(BaseModel):
    id: uuid.UUID
    filename: str
    acquisition_time: Optional[datetime.datetime]
    crs: Optional[str]
    width: int
    height: int
    resolution_x: Optional[float]
    resolution_y: Optional[float]


class BiTemporalPairResponse(BaseModel):
    pair_id: uuid.UUID
    image_t1: PairImageSummary
    image_t2: PairImageSummary
    acquisition_time_t1: Optional[datetime.datetime]
    acquisition_time_t2: Optional[datetime.datetime]
    spatially_compatible: bool
    temporally_valid: bool
    overlap_ratio: Optional[float]
    alignment_status: str
    registration_method: Optional[str]
    registration_metadata: Optional[Dict[str, Any]]
    validation: PairValidationResult
    created_at: datetime.datetime


class ChangeRegion(BaseModel):
    region_id: str
    label: str
    confidence: float
    bbox: List[float] = Field(..., description="Normalized [x1, y1, x2, y2] bbox (0.0 to 1.0)")
    pixel_geometry: Dict[str, int] = Field(..., description="Pixel coordinates {x1, y1, x2, y2, width, height}")
    geo_geometry: Optional[Dict[str, Any]] = Field(None, description="Native CRS bounds and GeoJSON polygon")
    pixel_area: int
    relative_area: float


class ChangeAnalysisRequest(BaseModel):
    pair_id: Optional[uuid.UUID] = Field(None, description="Pre-existing BiTemporalPair ID")
    image_t1_id: Optional[uuid.UUID] = Field(None, description="Earlier image T1 ID if creating ad-hoc")
    image_t2_id: Optional[uuid.UUID] = Field(None, description="Later image T2 ID if creating ad-hoc")
    query: Optional[str] = Field("What changed between these two images?", description="Natural language change question or directive")
    threshold: Optional[float] = Field(0.35, description="Binary change detection threshold (0.0 to 1.0)")
    min_region_size: Optional[int] = Field(25, description="Minimum connected pixel count to form a change region")


class ChangeAnalysisSummary(BaseModel):
    detected: bool
    change_score: float
    change_percentage: float
    regions_count: int
    threshold_used: Optional[float] = None



class ProcessingDetails(BaseModel):
    alignment_performed: bool
    registration_method: Optional[str]
    model: str
    model_version: str
    processing_time_ms: int


class ChangeAnalysisResponse(BaseModel):
    analysis_id: uuid.UUID
    task: str = "CHANGE_ANALYSIS"
    pair_id: uuid.UUID
    answer: str
    change: ChangeAnalysisSummary
    regions: List[ChangeRegion]
    confidence: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    processing: ProcessingDetails
    artifact_key: Optional[str] = None
    change_map_key: Optional[str] = None
    trace_id: Optional[str] = None


class ChangeVQARequest(BaseModel):
    pair_id: Optional[uuid.UUID] = None
    image_t1_id: Optional[uuid.UUID] = None
    image_t2_id: Optional[uuid.UUID] = None
    query: str = Field(..., description="Specific question regarding temporal modifications (e.g. 'Did urban area increase?')")
