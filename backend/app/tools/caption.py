"""
Single Image Scene Captioning Tool Adapter.
Delegates inference to AnalysisService and standardizes scene-description contracts.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analysis_service import AnalysisService
from app.tools.base import AnalysisTool


class SingleImageCaptionTool(AnalysisTool):
    """
    Tool adapter for generating natural-language scene descriptions for a single satellite image.
    Delegates lifecycle and model execution entirely to AnalysisService.
    """

    name = "single_image_caption"
    version = "1.0.0"
    task = "SCENE_DESCRIPTION"
    description = (
        "Generates automated natural-language descriptive summaries of terrain, land use, "
        "and structures visible in a single remote-sensing satellite image."
    )
    status = "available"

    supported_input_types = ["single_image"]
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]
    required_inputs = ["image_id"]
    optional_parameters = {
        "model_name": {"type": "string", "description": "Explicit specialist model name override"}
    }

    def validate_inputs(self, input_context: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        super().validate_inputs(input_context, parameters)
        image_id = parameters.get("image_id") or input_context.get("image_id")
        if not image_id:
            raise ValueError("Target image_id is required for scene captioning.")

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes single image captioning through AnalysisService.
        """
        image_id = parameters.get("image_id") or input_context.get("image_id")
        if isinstance(image_id, str):
            image_id = uuid.UUID(image_id)

        model_name = parameters.get("model_name")

        raw_result = await AnalysisService.analyze(
            task="image_captioning",
            image_id=image_id,
            model_name=model_name,
            db=db
        )

        return self.normalize_result(raw_result)

    def normalize_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes AnalysisService output into standard tool execution response.
        """
        result_inner = raw_result.get("result", {})
        caption = result_inner.get("caption", "")
        return {
            "analysis_id": raw_result.get("analysis_id"),
            "status": raw_result.get("status", "completed"),
            "task": self.task,
            "tool_name": self.name,
            "tool_version": self.version,
            "caption": caption,
            "answer": caption,  # Standardize textual output across tasks
            "confidence": {
                "score": raw_result.get("confidence", 0.0),
                "method": raw_result.get("confidence_method", "sequence_perplexity")
            },
            "evidence": raw_result.get("evidence", []),
            "model": raw_result.get("model"),
            "model_version": raw_result.get("model_version"),
            "processing_time_ms": raw_result.get("processing_time_ms", 0),
        }
