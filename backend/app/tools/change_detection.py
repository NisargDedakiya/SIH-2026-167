"""
Bi-Temporal Change Detection Tool.
Registered agent tool executing pair alignment, specialist model inference,
change map generation, and region extraction across verified image pairs.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.temporal.schemas import BiTemporalPairCreate
from app.temporal.service import get_temporal_service
from app.tools.base import AnalysisTool


class BiTemporalChangeDetectionTool(AnalysisTool):
    """
    Standardized AnalysisTool wrapper for bi-temporal remote-sensing change detection.
    """

    def __init__(self):
        self.name = "bi_temporal_change_detection"
        self.version = "0.1.0"
        self.task = "CHANGE_ANALYSIS"
        self.description = (
            "Executes bi-temporal co-registration, Siamese feature difference inference, "
            "change map generation, and region extraction across verified image pairs."
        )
        self.status = "available"
        self.supported_input_types = ["multi_image", "pair"]
        self.supported_modalities = ["optical", "multispectral", "sar", "unknown"]
        self.required_inputs = ["pair_id"]
        self.optional_parameters = {
            "query": "What changed between these two images?",
            "threshold": 0.35,
            "min_region_size": 25,
        }

    def validate_inputs(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        """Validates that a pair_id or two image_ids are present."""
        has_pair = "pair_id" in parameters or "pair_id" in input_context
        image_ids = input_context.get("image_ids", [])

        if not has_pair and len(image_ids) < 2:
            raise ValueError(
                f"Tool '{self.name}' requires either a 'pair_id' or at least 2 image IDs (T1 and T2)."
            )

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes change detection analysis through TemporalPairService.
        """
        temporal_svc = get_temporal_service()
        pair_id = parameters.get("pair_id") or input_context.get("pair_id")

        # If pair_id is not yet registered, register it on the fly
        if not pair_id:
            image_ids = input_context.get("image_ids", [])
            t1_id = uuid.UUID(str(image_ids[0]))
            t2_id = uuid.UUID(str(image_ids[1]))

            pair_resp = await temporal_svc.create_pair(
                BiTemporalPairCreate(image_t1_id=t1_id, image_t2_id=t2_id),
                db=db
            )
            pair_id = pair_resp.pair_id
        else:
            if isinstance(pair_id, str):
                pair_id = uuid.UUID(pair_id)

        query = parameters.get("query") or input_context.get("query") or "What changed between these two images?"
        threshold = float(parameters.get("threshold", 0.35))
        min_region_size = int(parameters.get("min_region_size", 25))

        change_res = await temporal_svc.execute_change_analysis(
            pair_id=pair_id,
            query=query,
            threshold=threshold,
            min_region_size=min_region_size,
            db=db
        )

        return {
            "task": "CHANGE_ANALYSIS",
            "model": {
                "name": change_res.processing.model,
                "version": change_res.processing.model_version
            },
            "answer": change_res.answer,
            "pair_id": str(pair_id),
            "regions": [r.model_dump() for r in change_res.regions],
            "change": change_res.change.model_dump(),
            "result": {
                "answer": change_res.answer,
                "changed": change_res.change.detected,
                "change_score": change_res.change.change_score,
                "change_percentage": change_res.change.change_percentage,
                "regions_count": change_res.change.regions_count,
                "regions": [r.model_dump() for r in change_res.regions],
                "pair_id": str(pair_id),
            },
            "confidence": change_res.confidence,
            "evidence": change_res.evidence,
            "artifact_key": change_res.artifact_key,
            "processing_time_ms": change_res.processing.processing_time_ms
        }
