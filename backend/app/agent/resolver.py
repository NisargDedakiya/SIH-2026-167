"""
Capability Resolver for SatQuery AI.
Validates whether the detected intent can be serviced given current phase capabilities,
available tool registry entries, and user-provided image configurations.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.agent.exceptions import CapabilityUnavailableError
from app.tools.base import AnalysisTool
from app.tools.registry import ToolRegistry, get_tool_registry


@dataclass
class ResolutionResult:
    is_executable: bool
    task: str
    tool: Optional[AnalysisTool]
    status_reason: str
    phase_availability: str  # "available_phase_3", "planned_phase_4", "planned_phase_5", "planned_phase_6", "unsupported"


class CapabilityResolver:
    """
    Evaluates detected task against the capability matrix and input configuration.
    Prevents silent fallbacks for recognized future tasks.
    """

    CAPABILITY_MATRIX = {
        "VISUAL_QUESTION_ANSWERING": {
            "phase": "Phase 2/3 (Active)",
            "required_images": 1,
            "supported_modalities": ["optical", "multispectral", "sar", "unknown"],
            "tool_name": "single_image_vqa",
            "is_executable": True,
        },
        "SCENE_DESCRIPTION": {
            "phase": "Phase 2/3 (Active)",
            "required_images": 1,
            "supported_modalities": ["optical", "multispectral", "sar", "unknown"],
            "tool_name": "single_image_caption",
            "is_executable": True,
        },
        "GROUNDING": {
            "phase": "Phase 4 (Active)",
            "required_images": 1,
            "supported_modalities": ["optical", "multispectral", "sar", "unknown"],
            "tool_name": "single_image_grounding",
            "is_executable": True,
        },
        "CHANGE_ANALYSIS": {
            "phase": "Phase 5 (Active)",
            "required_images": 2,
            "supported_modalities": ["optical", "multispectral", "sar", "unknown"],
            "tool_name": "bi_temporal_change_detection",
            "is_executable": True,
        },
        "CROSS_MODAL_ANALYSIS": {
            "phase": "Phase 6 (Active)",
            "required_images": 2,
            "supported_modalities": ["optical", "multispectral", "sar", "unknown"],
            "tool_name": "optical_sar_analysis",
            "is_executable": True,
        },
    }

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or get_tool_registry()

    def resolve(
        self,
        task: str,
        input_context: Dict[str, Any]
    ) -> ResolutionResult:
        """
        Resolves task compatibility against tool registry and input configuration.
        """
        task_upper = task.upper()
        num_images = input_context.get("number_of_images", 1)
        if input_context.get("pair_id") or input_context.get("pair"):
            num_images = max(num_images, 2)

        if task_upper not in self.CAPABILITY_MATRIX:
            return ResolutionResult(
                is_executable=False,
                task=task_upper,
                tool=None,
                status_reason=f"Task '{task_upper}' is not recognized in the capability matrix.",
                phase_availability="unsupported"
            )

        spec = self.CAPABILITY_MATRIX[task_upper]

        # Check executable status
        if not spec["is_executable"]:
            msg = spec.get("unavailable_message", f"Capability for '{task_upper}' is not available yet.")
            return ResolutionResult(
                is_executable=False,
                task=task_upper,
                tool=None,
                status_reason=msg,
                phase_availability=spec["phase"]
            )

        # Check image count constraint for executable tools
        if num_images < spec["required_images"]:
            return ResolutionResult(
                is_executable=False,
                task=task_upper,
                tool=None,
                status_reason=f"Task '{task_upper}' requires at least {spec['required_images']} image(s), but {num_images} provided.",
                phase_availability=spec["phase"]
            )

        # Find registered tool
        tool_name = spec["tool_name"]
        if task_upper == "CHANGE_ANALYSIS":
            q = input_context.get("query", "").lower().strip()
            if "describe" in q or "description" in q or "summary" in q:
                tool_name = "change_description"
            elif any(q.startswith(w) for w in ["did", "is", "has", "are", "where", "what type", "how many"]) or any(w in q for w in ["increase", "decrease", "more", "less", "new roads", "new buildings"]):
                tool_name = "bi_temporal_change_vqa"
            else:
                tool_name = "bi_temporal_change_detection"
        elif task_upper == "CROSS_MODAL_ANALYSIS":
            q = input_context.get("query", "").lower().strip()
            if any(q.startswith(w) for w in ["highlight", "locate", "outline", "bound", "where is", "where are", "draw"]):
                tool_name = "optical_sar_grounding"
            elif any(q.startswith(w) for w in ["what", "does", "which", "is", "are", "can", "how"]) or "reveal" in q or "differ" in q or "?" in q:
                tool_name = "optical_sar_vqa"
            else:
                tool_name = "optical_sar_analysis"

        tool = self.registry.get(tool_name)
        if not tool or tool.status != "available":
            return ResolutionResult(
                is_executable=False,
                task=task_upper,
                tool=None,
                status_reason=f"Required tool '{tool_name}' for task '{task_upper}' is not available in registry.",
                phase_availability="unsupported"
            )

        return ResolutionResult(
            is_executable=True,
            task=task_upper,
            tool=tool,
            status_reason=f"Task '{task_upper}' mapped successfully to registered tool '{tool.name}'.",
            phase_availability=spec["phase"]
        )
