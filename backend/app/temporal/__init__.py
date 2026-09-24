"""
Bi-Temporal Remote-Sensing Analysis Subsystem.
Handles temporal pair validation, spatial overlap analysis, controlled alignment,
change detection inference, change region extraction, and temporal reasoning.
"""

from app.database.models import BiTemporalPairModel
from app.temporal.schemas import (
    BiTemporalPairCreate,
    BiTemporalPairResponse,
    PairValidationResult,
    ChangeAnalysisRequest,
    ChangeAnalysisResponse,
    ChangeRegion,
)
from app.temporal.compatibility import SpatialCompatibilityChecker
from app.temporal.validator import BiTemporalValidator
from app.temporal.alignment import AlignmentEngine
from app.temporal.change_map import ChangeMap
from app.temporal.regions import ChangeRegionExtractor
from app.temporal.description import ChangeDescriptionEngine
from app.temporal.change_vqa import ChangeVQAEngine
from app.temporal.service import TemporalPairService, get_temporal_service

__all__ = [
    "BiTemporalPairModel",
    "BiTemporalPairCreate",
    "BiTemporalPairResponse",
    "PairValidationResult",
    "ChangeAnalysisRequest",
    "ChangeAnalysisResponse",
    "ChangeRegion",
    "SpatialCompatibilityChecker",
    "BiTemporalValidator",
    "AlignmentEngine",
    "ChangeMap",
    "ChangeRegionExtractor",
    "ChangeDescriptionEngine",
    "ChangeVQAEngine",
    "TemporalPairService",
    "get_temporal_service",
]
