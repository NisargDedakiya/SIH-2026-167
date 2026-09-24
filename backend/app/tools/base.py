"""
Base interface and abstractions for SatQuery Analysis Tools.
Every specialist tool must inherit from AnalysisTool and adhere to strict parameter contracts.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class AnalysisTool(ABC):
    """
    Abstract Base Class for all analytical tools managed by the ToolRegistry.
    Tools act as adapters bridging the Agent orchestrator and underlying specialist services.
    """

    name: str
    version: str
    task: str
    description: str
    status: str = "available"  # "available" or "planned"

    supported_input_types: List[str] = ["single_image"]
    supported_modalities: List[str] = ["optical", "multispectral", "sar", "unknown"]
    required_inputs: List[str] = ["image_id"]
    optional_parameters: Dict[str, Any] = {}

    def validate_inputs(self, input_context: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        """
        Validates that all required inputs and parameter types are satisfied.
        Raises ValueError or ParameterValidationError if validation fails.
        """
        for req in self.required_inputs:
            if req not in parameters and req not in input_context:
                raise ValueError(f"Tool '{self.name}' requires input '{req}', which was not provided.")

        # Modality check if provided in context
        image_modality = input_context.get("modality", "unknown").lower()
        if image_modality not in [m.lower() for m in self.supported_modalities]:
            raise ValueError(
                f"Modality '{image_modality}' is not supported by tool '{self.name}'. "
                f"Supported: {self.supported_modalities}"
            )

    def get_schema(self) -> Dict[str, Any]:
        """Returns structured JSON schema declaring tool inputs, parameters, and metadata."""
        return {
            "name": self.name,
            "version": self.version,
            "task": self.task,
            "description": self.description,
            "status": self.status,
            "supported_input_types": self.supported_input_types,
            "supported_modalities": self.supported_modalities,
            "required_inputs": self.required_inputs,
            "optional_parameters": self.optional_parameters,
        }

    @abstractmethod
    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes the specialist analytical task.
        Must NOT perform arbitrary code or shell execution.
        """
        pass

    def normalize_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts raw execution output into standard contract:
        answer, confidence, evidence, processing_time_ms.
        """
        return raw_result
