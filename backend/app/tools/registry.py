"""
ToolRegistry for SatQuery AI.
Maintains all permitted analytical tools, validates availability, and resolves compatible tools.
"""

from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.tools.base import AnalysisTool
from app.tools.caption import SingleImageCaptionTool
from app.tools.change_description import ChangeDescriptionTool
from app.tools.change_detection import BiTemporalChangeDetectionTool
from app.tools.change_vqa import BiTemporalChangeVQATool
from app.tools.grounding import SingleImageGroundingTool
from app.tools.optical_sar_analysis import OpticalSARAnalysisTool
from app.tools.optical_sar_grounding import OpticalSARGroundingTool
from app.tools.optical_sar_vqa import OpticalSARVQATool
from app.tools.vqa import SingleImageVQATool


class PlannedTool(AnalysisTool):
    """
    Placeholder descriptor for planned capabilities in upcoming phases.
    Cannot be executed in Phase 3.
    """

    def __init__(
        self,
        name: str,
        version: str,
        task: str,
        description: str,
        supported_input_types: List[str],
        supported_modalities: List[str],
        required_inputs: List[str],
    ):
        self.name = name
        self.version = version
        self.task = task
        self.description = description
        self.status = "planned"
        self.supported_input_types = supported_input_types
        self.supported_modalities = supported_modalities
        self.required_inputs = required_inputs
        self.optional_parameters = {}

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[Any] = None
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            f"Tool '{self.name}' for task '{self.task}' is a planned capability and not available in Phase 3."
        )


class ToolRegistry:
    """
    Central registry for analytical tools.
    Enforces that the Agent only plans and executes verified, registered tools.
    """

    def __init__(self):
        self._tools: Dict[str, AnalysisTool] = {}
        self._task_index: Dict[str, List[str]] = {}

    def register(self, tool: AnalysisTool) -> None:
        """Registers a tool in the registry and indexes it by task."""
        self._tools[tool.name] = tool
        task_key = tool.task.upper()
        if task_key not in self._task_index:
            self._task_index[task_key] = []
        if tool.name not in self._task_index[task_key]:
            self._task_index[task_key].append(tool.name)
        logger.info(f"Registered tool '{tool.name}' (v{tool.version}) for task '{tool.task}' [{tool.status}].")

    def get(self, name: str) -> Optional[AnalysisTool]:
        """Retrieves a registered tool by name."""
        return self._tools.get(name)

    def list(self) -> List[AnalysisTool]:
        """Returns all registered tools (both available and planned)."""
        return list(self._tools.values())

    def list_available(self) -> List[AnalysisTool]:
        """Returns only currently executable tools."""
        return [t for t in self._tools.values() if t.status == "available"]

    def find_by_task(self, task: str) -> List[AnalysisTool]:
        """Finds registered tools capable of performing the specified task."""
        tool_names = self._task_index.get(task.upper(), [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def find_compatible_tools(self, input_context: Dict[str, Any]) -> List[AnalysisTool]:
        """
        Finds available tools compatible with the provided input context
        (e.g., number of images, modality).
        """
        image_count = input_context.get("number_of_images", 1)
        modality = input_context.get("modality", "unknown").lower()

        compatible = []
        for tool in self.list_available():
            # Check input type compatibility
            if image_count == 1 and "single_image" not in tool.supported_input_types:
                continue
            if image_count > 1 and "multi_image" not in tool.supported_input_types:
                continue

            # Check modality compatibility
            if modality not in [m.lower() for m in tool.supported_modalities]:
                continue

            compatible.append(tool)

        return compatible


# Global singleton registry
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Returns initialized ToolRegistry with default Phase 3 and planned Phase 4-6 tools."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()

        # Phase 3, 4 & 5 Available Tools
        _tool_registry.register(SingleImageVQATool())
        _tool_registry.register(SingleImageCaptionTool())
        _tool_registry.register(SingleImageGroundingTool())
        _tool_registry.register(BiTemporalChangeDetectionTool())
        _tool_registry.register(BiTemporalChangeVQATool())
        _tool_registry.register(ChangeDescriptionTool())

        # Phase 6 Optical-SAR Cross-Modal Tools
        _tool_registry.register(OpticalSARAnalysisTool())
        _tool_registry.register(OpticalSARVQATool())
        _tool_registry.register(OpticalSARGroundingTool())

    return _tool_registry
