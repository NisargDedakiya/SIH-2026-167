"""
Single Image Visual Question Answering (VQA) Tool Adapter.
Delegates inference to AnalysisService and standardizes query-answering contracts.
"""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analysis_service import AnalysisService
from app.tools.base import AnalysisTool


class SingleImageVQATool(AnalysisTool):
    """
    Tool adapter for executing Visual Question Answering against a single satellite image.
    Delegates lifecycle and model execution entirely to AnalysisService.
    """

    name = "single_image_vqa"
    version = "1.0.0"
    task = "VISUAL_QUESTION_ANSWERING"
    description = (
        "Answers natural language questions about land cover, infrastructure, and terrain "
        "features visible in a single remote-sensing satellite image."
    )
    status = "available"

    supported_input_types = ["single_image"]
    supported_modalities = ["optical", "multispectral", "sar", "unknown"]
    required_inputs = ["image_id", "query"]
    optional_parameters = {
        "model_name": {"type": "string", "description": "Explicit specialist model name override"}
    }

    def validate_inputs(self, input_context: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        super().validate_inputs(input_context, parameters)
        query = parameters.get("query") or input_context.get("query")
        if not query or not str(query).strip():
            raise ValueError("Query string is required and cannot be empty for Visual QA.")

        image_id = parameters.get("image_id") or input_context.get("image_id")
        if not image_id:
            raise ValueError("Target image_id is required for Visual QA.")

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes single image VQA through AnalysisService.
        """
        image_id = parameters.get("image_id") or input_context.get("image_id")
        if isinstance(image_id, str):
            image_id = uuid.UUID(image_id)

        query = str(parameters.get("query") or input_context.get("query", "")).strip()
        model_name = parameters.get("model_name")

        raw_result = await AnalysisService.analyze(
            task="visual_question_answering",
            image_id=image_id,
            query=query,
            model_name=model_name,
            db=db
        )

        return self.normalize_result(raw_result)

    def normalize_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes AnalysisService output into standard tool execution response.
        """
        result_inner = raw_result.get("result", {})
        answer = result_inner.get("answer", "")
        model_name = raw_result.get("model", "")
        is_adapted = (model_name == "satquery-rs-v1") or ("adapter_metadata" in result_inner)

        return {
            "analysis_id": raw_result.get("analysis_id"),
            "status": raw_result.get("status", "completed"),
            "task": self.task,
            "tool_name": self.name,
            "tool_version": self.version,
            "answer": answer,
            "confidence": {
                "score": raw_result.get("confidence", 0.0),
                "method": raw_result.get("confidence_method", "token_probability")
            },
            "evidence": raw_result.get("evidence", []),
            "model": model_name,
            "model_version": raw_result.get("model_version"),
            "processing_time_ms": raw_result.get("processing_time_ms", 0),
            "is_adapted": is_adapted,
            "adapter_metadata": result_inner.get("adapter_metadata") or raw_result.get("adapter_metadata"),
            "fallback": raw_result.get("fallback"),
        }
