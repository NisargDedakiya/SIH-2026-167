"""
Optical-SAR Cross-Modal Analysis Tool for SatQuery AI.
Registered Agent tool executing co-registration, feature fusion,
and joint multimodal interpretation across Optical and SAR pairs.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.cross_modal.schemas import OpticalSARPairCreate
from app.cross_modal.service import get_cross_modal_service
from app.tools.base import AnalysisTool


class OpticalSARAnalysisTool(AnalysisTool):
    """
    Standardized AnalysisTool wrapper for Optical-SAR cross-modal analysis.
    """

    def __init__(self):
        self.name = "optical_sar_analysis"
        self.version = "1.0.0"
        self.task = "CROSS_MODAL_ANALYSIS"
        self.description = (
            "Executes non-destructive co-registration, Stage B feature fusion, "
            "and Stage C joint multimodal reasoning across Optical and SAR image pairs."
        )
        self.status = "available"
        self.supported_input_types = ["multi_image", "pair"]
        self.supported_modalities = ["optical", "multispectral", "sar"]
        self.required_inputs = ["pair_id"]
        self.optional_parameters = {
            "query": "Analyze these optical and SAR images together.",
        }

    def validate_inputs(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        """Validates that a pair_id or optical + SAR image_ids are present."""
        has_pair = "pair_id" in parameters or "pair_id" in input_context
        image_ids = input_context.get("image_ids", [])

        if not has_pair and len(image_ids) < 2:
            raise ValueError(
                f"Tool '{self.name}' requires either a registered 'pair_id' or 2 satellite image IDs (Optical and SAR)."
            )

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes cross-modal analysis through CrossModalPairService.
        """
        service = get_cross_modal_service()
        pair_id = parameters.get("pair_id") or input_context.get("pair_id")

        if not pair_id:
            image_ids = input_context.get("image_ids", [])
            opt_id = uuid.UUID(str(image_ids[0]))
            sar_id = uuid.UUID(str(image_ids[1]))

            pair_resp = await service.create_pair(
                OpticalSARPairCreate(optical_image_id=opt_id, sar_image_id=sar_id),
                db=db
            )
            pair_id = pair_resp.id
        else:
            if isinstance(pair_id, str):
                pair_id = uuid.UUID(pair_id)

        query = parameters.get("query") or input_context.get("query") or "Analyze these optical and SAR images together."

        res = await service.execute_cross_modal_analysis(
            pair_id=pair_id,
            query=query,
            task="cross_modal_analysis",
            db=db
        )

        return {
            "task": "CROSS_MODAL_ANALYSIS",
            "model": {
                "name": res.processing.get("model", "optical-sar-fusion-baseline"),
                "version": "1.0.0"
            },
            "modalities": {
                "optical": res.optical_summary.modality,
                "sar": res.sar_summary.modality
            },
            "result": {
                "answer": res.answer,
                "observations": res.joint_observations,
                "optical_contribution": res.optical_summary.contribution,
                "sar_contribution": res.sar_summary.contribution,
                "disagreement_status": res.disagreement.agreement_status,
                "disagreement_explanation": res.disagreement.explanation,
            },
            "confidence": res.confidence,
            "evidence": res.evidence,
            "regions": [r.model_dump() for r in res.regions],
            "pair_id": str(pair_id),
            "processing_time_ms": res.processing.get("duration_ms", 0),
        }
