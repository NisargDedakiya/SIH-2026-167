"""
Unified Data Schema for SatQuery AI Analysis Reports (Part 24).
Single authoritative schema driving JSON, HTML, PDF, and Package exports.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReportInputImage(BaseModel):
    image_id: str
    role: str = "primary"  # primary, t1, t2, optical, sar
    filename: str
    modality: str
    sensor: Optional[str] = None
    acquisition_date: Optional[str] = None
    resolution_m: Optional[float] = None
    crs: Optional[str] = None
    epsg_code: Optional[int] = None
    dimensions: str
    is_geospatial: bool = False
    validation_status: str = "valid"


class ReportEvidenceItem(BaseModel):
    evidence_id: str
    type: str  # bounding_box, change_mask, overlay, crop
    label: str
    confidence: Optional[float] = None
    pixel_coordinates: Optional[Any] = None
    geographic_coordinates: Optional[Any] = None
    artifact_key: Optional[str] = None


class ReportObservations(BaseModel):
    observed: List[str] = Field(default_factory=list)
    inferred: List[str] = Field(default_factory=list)
    uncertain: List[str] = Field(default_factory=list)


class ReportModelDetails(BaseModel):
    name: str
    version: str
    task: str
    is_adapted: bool = False
    adapter_type: Optional[str] = None
    dataset_provenance: Optional[str] = None
    base_model: Optional[str] = None
    device: str = "CPU (Pure PyTorch)"


class ReportExecutionMilestone(BaseModel):
    sequence: int
    milestone: str
    status: str
    timestamp: str
    duration_ms: Optional[int] = None


class AnalysisReport(BaseModel):
    """
    Comprehensive normalized analysis report.
    Fed directly to HTML, PDF, JSON, and ZIP Package exporters.
    """
    report_id: str
    analysis_id: str
    generated_at: str
    report_version: str = "1.0.0"
    analysis_version: str = "1.0.0 (Phase 9)"
    system_title: str = "SatQuery AI — Multimodal Earth Observation Analysis"
    problem_statement: str = "ISRO Smart India Hackathon · Problem Statement 26167"

    # Query & Task
    query: str
    detected_task: str

    # Answer & Synthesis
    answer: str
    confidence_score: Optional[float] = None
    confidence_percentage: Optional[str] = None
    confidence_method: Optional[str] = None
    calibration_status: str = "Calibrated"

    # Inputs & Modalities
    inputs: List[ReportInputImage] = Field(default_factory=list)

    # Visual Evidence
    evidence: List[ReportEvidenceItem] = Field(default_factory=list)

    # Structured Observations
    observations: ReportObservations = Field(default_factory=ReportObservations)

    # Model & Execution
    models: List[ReportModelDetails] = Field(default_factory=list)
    execution_milestones: List[ReportExecutionMilestone] = Field(default_factory=list)
    total_processing_time_ms: int = 0

    # Operational Limitations
    limitations: List[str] = Field(default_factory=list)

    # Reproducibility & Trace Audit
    agent_run_id: Optional[str] = None
    trace_audit_available: bool = False
    reproducibility_token: str = ""
