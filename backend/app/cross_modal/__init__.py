"""
Optical-SAR Cross-Modal Intelligence Domain Package.
Provides pair lifecycle management, spatial compatibility evaluation,
non-destructive co-registration, feature fusion, task-specific reasoning,
and API service coordination.
"""

from app.cross_modal.alignment import CrossModalAlignmentEngine
from app.cross_modal.compatibility import CrossModalSpatialCompatibility
from app.cross_modal.fusion import CrossModalFusion
from app.cross_modal.models import OpticalSARPair, OpticalSARPairModel
from app.cross_modal.reasoning import CrossModalReasoningEngine
from app.cross_modal.schemas import (
    CrossModalAnalysisRequest,
    CrossModalAnalysisResponse,
    CrossModalEvidenceRegion,
    CrossModalValidationResult,
    ModalityContribution,
    ModalityDisagreement,
    OpticalSARPairCreate,
    OpticalSARPairResponse,
    PairImageSummary,
)
from app.cross_modal.service import CrossModalPairService, get_cross_modal_service
from app.cross_modal.validator import CrossModalValidator

__all__ = [
    "OpticalSARPair",
    "OpticalSARPairModel",
    "CrossModalValidator",
    "CrossModalSpatialCompatibility",
    "CrossModalAlignmentEngine",
    "CrossModalFusion",
    "CrossModalReasoningEngine",
    "CrossModalPairService",
    "get_cross_modal_service",
    "OpticalSARPairCreate",
    "OpticalSARPairResponse",
    "PairImageSummary",
    "CrossModalValidationResult",
    "CrossModalAnalysisRequest",
    "CrossModalAnalysisResponse",
    "ModalityContribution",
    "ModalityDisagreement",
    "CrossModalEvidenceRegion",
]
