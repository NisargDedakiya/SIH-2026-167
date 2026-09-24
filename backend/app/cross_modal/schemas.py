"""
Pydantic Schemas for Optical-SAR Cross-Modal Subsystem.
Defines strict API contracts for pair creation, validation, analysis, VQA, and grounding.
"""

import datetime
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OpticalSARPairCreate(BaseModel):
    """Payload to register and validate an Optical-SAR pair."""
    optical_image_id: uuid.UUID = Field(..., description="ID of the Optical or Multispectral image record")
    sar_image_id: uuid.UUID = Field(..., description="ID of the Synthetic Aperture Radar image record")


class PairImageSummary(BaseModel):
    """Compact summary of a registered satellite image within a pair."""
    id: uuid.UUID
    original_filename: str
    modality: str
    sensor: Optional[str] = None
    crs: Optional[str] = None
    resolution: Optional[float] = None
    bounds: Optional[Dict[str, Any]] = None
    acquisition_time: Optional[datetime.datetime] = None
    band_count: int
    dtype: str
    polarization: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CrossModalValidationResult(BaseModel):
    """Detailed result of spatial and modality validation for an Optical-SAR pair."""
    valid: bool
    optical_valid: bool
    sar_valid: bool
    spatially_compatible: bool
    overlap_ratio: float
    status_code: str
    message: str
    optical_modality: str
    sar_modality: str
    sar_polarization: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class OpticalSARPairResponse(BaseModel):
    """Full representation of a registered Optical-SAR image pair."""
    id: uuid.UUID
    optical_image: PairImageSummary
    sar_image: PairImageSummary
    optical_modality: str
    sar_modality: str
    optical_sensor: Optional[str] = None
    sar_sensor: Optional[str] = None
    spatial_compatibility: str
    registration_status: str
    validation_status: str
    overlap_ratio: Optional[float] = None
    alignment_method: Optional[str] = None
    alignment_metadata: Optional[Dict[str, Any]] = None
    validation: CrossModalValidationResult
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class ModalityContribution(BaseModel):
    """Structured breakdown of what a specific modality contributes to the joint analysis."""
    available: bool
    modality: str
    sensor: Optional[str] = None
    contribution: str
    features: List[str] = Field(default_factory=list)


class ModalityDisagreement(BaseModel):
    """Structured report of agreement or divergence between Optical and SAR evidence."""
    agreement_status: str  # AGREEMENT, PARTIAL_AGREEMENT, DISAGREEMENT, INSUFFICIENT_EVIDENCE
    disagreement_type: Optional[str] = None
    explanation: str


class CrossModalEvidenceRegion(BaseModel):
    """Spatial evidence region localized across optical and SAR modalities."""
    id: str
    label: str
    confidence: float
    bbox: List[float] = Field(..., description="Normalized [ymin, xmin, ymax, xmax] relative to raster grid")
    pixel_geometry: Dict[str, Any] = Field(..., description="Absolute pixel bounding box {x1, y1, x2, y2, w, h}")
    geo_geometry: Optional[Dict[str, Any]] = Field(None, description="Native CRS bounding coordinates")
    supported_by: str = Field("both", description="'optical', 'sar', or 'both'")
    rationale: Optional[str] = None


class CrossModalAnalysisRequest(BaseModel):
    """Payload to execute cross-modal joint reasoning or VQA."""
    pair_id: uuid.UUID = Field(..., description="Registered OpticalSARPair ID")
    query: Optional[str] = Field(
        default="Analyze these optical and SAR images together.",
        description="Natural language instruction or question"
    )
    task: Optional[str] = Field(
        default="cross_modal_analysis",
        description="Target task: 'cross_modal_analysis', 'cross_modal_vqa', or 'cross_modal_grounding'"
    )


class CrossModalAnalysisResponse(BaseModel):
    """Comprehensive analysis response combining joint reasoning, modality details, and evidence."""
    analysis_id: uuid.UUID
    task: str
    pair_id: uuid.UUID
    query: str
    answer: str
    optical_summary: ModalityContribution
    sar_summary: ModalityContribution
    joint_observations: List[str]
    disagreement: ModalityDisagreement
    regions: List[CrossModalEvidenceRegion]
    confidence: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    processing: Dict[str, Any]
