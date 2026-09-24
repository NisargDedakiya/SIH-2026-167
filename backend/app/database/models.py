import datetime
import uuid
from typing import Any, Dict, Optional
import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    Text,
    Uuid,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ImageModel(Base):
    """
    Core remote-sensing image registry record.
    Represents an ingested raster file with extracted technical and geospatial metadata.
    """
    __tablename__ = "images"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    preview_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)  # GeoTIFF, TIFF, PNG, JPEG
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256

    # Raster specifications
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    band_count: Mapped[int] = mapped_column(Integer, nullable=False)
    dtype: Mapped[str] = mapped_column(String(32), nullable=False)
    nodata: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Geospatial referencing
    crs: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    epsg_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolution_x: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution_y: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    transform: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    # Remote Sensing domain tags
    acquisition_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sensor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    modality: Mapped[str] = mapped_column(String(64), default="unknown", nullable=False)
    is_geospatial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Validation & Lifecycle
    validation_status: Mapped[str] = mapped_column(String(32), default="valid", nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )

    # Relationships
    metadata_entries: Mapped[list["ImageMetadataModel"]] = relationship(
        "ImageMetadataModel", back_populates="image", cascade="all, delete-orphan"
    )
    analysis_jobs: Mapped[list["AnalysisJobModel"]] = relationship(
        "AnalysisJobModel", back_populates="image", cascade="all, delete-orphan"
    )
    evidence_records: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="image", cascade="all, delete-orphan"
    )


class ImageMetadataModel(Base):
    """
    Extensible metadata store for satellite-specific or future model outputs.
    Allows arbitrary JSON documents without mutating the core images table.
    """
    __tablename__ = "image_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    image: Mapped["ImageModel"] = relationship("ImageModel", back_populates="metadata_entries")


class AnalysisJobModel(Base):
    """
    Persistent inference record for remote-sensing AI queries (VQA, captioning, grounding).
    Tracks end-to-end lifecycle states:
    QUEUED -> VALIDATING -> PREPROCESSING -> RUNNING -> POSTPROCESSING -> COMPLETED (or FAILED)
    """
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pair_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bi_temporal_pairs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cross_modal_pair_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("optical_sar_pairs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # visual_question_answering, image_captioning, grounding, change_analysis, cross_modal_analysis
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="queued", nullable=False, index=True
    )  # queued, validating, preprocessing, running, postprocessing, completed, failed
    result_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    started_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    image: Mapped["ImageModel"] = relationship("ImageModel", back_populates="analysis_jobs")
    pair: Mapped[Optional["BiTemporalPairModel"]] = relationship("BiTemporalPairModel", back_populates="analysis_jobs")
    cross_modal_pair: Mapped[Optional["OpticalSARPairModel"]] = relationship(
        "OpticalSARPairModel", back_populates="analysis_jobs"
    )
    evidence_records: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="analysis_job", cascade="all, delete-orphan"
    )


class AgentRunModel(Base):
    """
    Persistent record of an Agent orchestration execution.
    Tracks user intent classification, workflow plan, execution status, and timing.
    """
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    analysis_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True), nullable=True, index=True
    )
    original_query: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_query: Mapped[str] = mapped_column(Text, nullable=False)
    detected_task: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    classification_confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    selected_tools: Mapped[Any] = mapped_column(JSON, default=list, nullable=False)
    plan_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="started", nullable=False, index=True
    )  # started, completed, unavailable, ambiguous, failed
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    confidence_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    trace_events: Mapped[list["AgentTraceEventModel"]] = relationship(
        "AgentTraceEventModel",
        back_populates="agent_run",
        cascade="all, delete-orphan",
        order_by="AgentTraceEventModel.sequence",
    )


class AgentTraceEventModel(Base):
    """
    Fine-grained observable audit event recorded during an Agent run.
    Contains ONLY observable execution facts — no private chain-of-thought.
    """
    __tablename__ = "agent_trace_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    parameters_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    output_metadata_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    agent_run: Mapped["AgentRunModel"] = relationship(
        "AgentRunModel", back_populates="trace_events"
    )


class EvidenceModel(Base):
    """
    Persistent visual evidence record for remote-sensing spatial grounding.
    Stores pixel coordinates, native CRS coordinates, bounding geometry, and artifact references.
    """
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(64), default="bounding_box", nullable=False
    )  # bounding_box, segmentation_mask, crop, coordinate
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Coordinates & Geometry
    geometry_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # Normalized [0..1] bbox/polygon
    pixel_geometry_json: Mapped[Any] = mapped_column(JSON, nullable=False)  # Original raster pixels {x1, y1, x2, y2, w, h}
    geo_geometry_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # CRS bounds {crs, min_x, min_y, max_x, max_y}

    # Artifact keys in Object Storage
    artifact_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # Full visual overlay
    crop_artifact_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # Region crop

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    analysis_job: Mapped["AnalysisJobModel"] = relationship(
        "AnalysisJobModel", back_populates="evidence_records"
    )
    image: Mapped["ImageModel"] = relationship(
        "ImageModel", back_populates="evidence_records"
    )


class BiTemporalPairModel(Base):
    """
    Persistent bi-temporal image pair for remote-sensing change analysis.
    Explicitly couples T1 (earlier image) and T2 (later image) with validation,
    spatial overlap calculations, and non-destructive alignment metadata.
    """
    __tablename__ = "bi_temporal_pairs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    image_t1_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_t2_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Acquisition timestamps
    acquisition_time_t1: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acquisition_time_t2: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Spatial & Temporal validation
    spatially_compatible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    temporally_valid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overlap_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # CRS & Geospatial specifications
    crs_t1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    crs_t2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    resolution_t1: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution_t2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounds_t1: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    bounds_t2: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Alignment & Co-registration tracking
    alignment_status: Mapped[str] = mapped_column(
        String(32), default="NOT_REQUIRED", nullable=False
    )  # NOT_REQUIRED, REPROJECTED, RESAMPLED, REGISTERED, FAILED
    registration_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    registration_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Detailed structured validation result
    validation_result_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationships
    image_t1: Mapped["ImageModel"] = relationship(
        "ImageModel", foreign_keys=[image_t1_id]
    )
    image_t2: Mapped["ImageModel"] = relationship(
        "ImageModel", foreign_keys=[image_t2_id]
    )
    analysis_jobs: Mapped[list["AnalysisJobModel"]] = relationship(
        "AnalysisJobModel", back_populates="pair", cascade="all, delete-orphan"
    )


class OpticalSARPairModel(Base):
    """
    Persistent Optical + SAR cross-modal image pair.
    Explicitly couples an Optical/Multispectral image with a SAR image,
    tracking spatial compatibility, co-registration details,
    modality-specific metadata, and non-destructive alignment metadata.
    """
    __tablename__ = "optical_sar_pairs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    optical_image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sar_image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Modalities and sensors
    optical_modality: Mapped[str] = mapped_column(String(64), default="optical", nullable=False)
    sar_modality: Mapped[str] = mapped_column(String(64), default="sar", nullable=False)
    optical_sensor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    sar_sensor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Acquisition timestamps
    optical_acquisition_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sar_acquisition_time: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # CRS & Geospatial specifications
    optical_crs: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sar_crs: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    optical_resolution: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sar_resolution: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    optical_bounds: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    sar_bounds: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Validation & compatibility
    registration_status: Mapped[str] = mapped_column(
        String(32), default="UNALIGNED", nullable=False
    )  # ALIGNED, REPROJECTED, RESAMPLED, UNALIGNED, FAILED
    spatial_compatibility: Mapped[str] = mapped_column(
        String(32), default="COMPATIBLE", nullable=False
    )  # COMPATIBLE, PARTIALLY_COMPATIBLE, INCOMPATIBLE, INSUFFICIENT_METADATA
    validation_status: Mapped[str] = mapped_column(
        String(32), default="VALID", nullable=False
    )  # VALID, INVALID, WARNING
    overlap_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Alignment tracking
    alignment_method: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    alignment_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    validation_result_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    # Relationships
    optical_image: Mapped["ImageModel"] = relationship(
        "ImageModel", foreign_keys=[optical_image_id]
    )
    sar_image: Mapped["ImageModel"] = relationship(
        "ImageModel", foreign_keys=[sar_image_id]
    )
    analysis_jobs: Mapped[list["AnalysisJobModel"]] = relationship(
        "AnalysisJobModel", back_populates="cross_modal_pair", cascade="all, delete-orphan"
    )



