"""
Single Image Visual Grounding Tool Adapter.
Delegates spatial referring expression localization to AnalysisService and formats visual evidence.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analysis_service import AnalysisService
from app.tools.base import AnalysisTool


class SingleImageGroundingTool(AnalysisTool):
    """
    Tool adapter for executing Visual Grounding on a single remote-sensing satellite image.
    Delegates inference, coordinate projection, and evidence artifact generation to AnalysisService.
    """

    name = "single_image_grounding"
    version = "1.0.0"
    task = "GROUNDING"
    description = (
        "Locates, highlights, and extracts spatial bounding boxes, pixel coordinates, "
        "and visual evidence overlays for natural-language referring expressions in satellite imagery."
    )
    status = "available"

    supported_input_types = ["single_image"]
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]
    required_inputs = ["image_id", "query"]
    optional_parameters = {
        "model_name": {"type": "string", "description": "Explicit specialist grounding model override"}
    }

    def validate_inputs(self, input_context: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        super().validate_inputs(input_context, parameters)
        query = parameters.get("query") or input_context.get("query")
        if not query or not str(query).strip():
            raise ValueError("Query / referring expression is required for visual grounding.")

        image_id = parameters.get("image_id") or input_context.get("image_id")
        if not image_id:
            raise ValueError("Target image_id is required for visual grounding.")

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes single image grounding through AnalysisService.
        """
        image_id = parameters.get("image_id") or input_context.get("image_id")
        if isinstance(image_id, str):
            image_id = uuid.UUID(image_id)

        query = str(parameters.get("query") or input_context.get("query", "")).strip()
        model_name = parameters.get("model_name")

        raw_result = await AnalysisService.analyze(
            task="grounding",
            image_id=image_id,
            query=query,
            model_name=model_name,
            db=db
        )

        return self.normalize_result(raw_result)

    def normalize_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes AnalysisService output into standard tool execution response with visual evidence.
        """
        result_inner = raw_result.get("result", {})
        answer = result_inner.get("answer", "")
        regions = result_inner.get("regions", [])
        evidence_items = raw_result.get("evidence", [])

        # Derive primary overlay artifact key if present in evidence
        artifact_key = None
        for ev in evidence_items:
            if isinstance(ev, dict) and ev.get("artifact_key"):
                artifact_key = ev["artifact_key"]
                break

        return {
            "analysis_id": raw_result.get("analysis_id"),
            "status": raw_result.get("status", "completed"),
            "task": self.task,
            "tool_name": self.name,
            "tool_version": self.version,
            "answer": answer,
            "regions": regions,
            "evidence": evidence_items,
            "artifact_key": artifact_key,
            "confidence": {
                "score": raw_result.get("confidence", 0.0),
                "method": raw_result.get("confidence_method", "detection_confidence")
            },
            "model": raw_result.get("model"),
            "model_version": raw_result.get("model_version"),
            "processing_time_ms": raw_result.get("processing_time_ms", 0),
        }
