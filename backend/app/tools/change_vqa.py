"""
Bi-Temporal Change Visual Question Answering (Change VQA) Tool.
Answers natural-language analytical questions regarding temporal modifications
between bi-temporal image acquisitions.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.temporal.schemas import BiTemporalPairCreate
from app.temporal.service import get_temporal_service
from app.tools.base import AnalysisTool


class BiTemporalChangeVQATool(AnalysisTool):
    """
    Standardized AnalysisTool wrapper for bi-temporal remote-sensing question answering.
    """

    def __init__(self):
        self.name = "bi_temporal_change_vqa"
        self.version = "0.1.0"
        self.task = "CHANGE_ANALYSIS"
        self.description = (
            "Answers natural-language questions targeting temporal modifications, "
            "land-use transitions, and spatial shifts between verified image pairs."
        )
        self.status = "available"
        self.supported_input_types = ["multi_image", "pair"]
        self.supported_modalities = ["optical", "multispectral", "sar", "unknown"]
        self.required_inputs = ["query"]
        self.optional_parameters = {
            "pair_id": None,
            "threshold": 0.35,
        }

    def validate_inputs(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> None:
        has_pair = "pair_id" in parameters or "pair_id" in input_context
        image_ids = input_context.get("image_ids", [])
        if not has_pair and len(image_ids) < 2:
            raise ValueError(f"Tool '{self.name}' requires either a 'pair_id' or 2 image IDs (T1 and T2).")

        query = parameters.get("query") or input_context.get("query")
        if not query or not str(query).strip():
            raise ValueError(f"Tool '{self.name}' requires a non-empty natural-language question.")

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        temporal_svc = get_temporal_service()
        pair_id = parameters.get("pair_id") or input_context.get("pair_id")

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

        change_res = await temporal_svc.execute_change_analysis(
            pair_id=pair_id,
            query=query,
            threshold=threshold,
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
