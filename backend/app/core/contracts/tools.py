from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel


class ToolMetadata(BaseModel):
    name: str
    description: str
    required_inputs: List[str]
    supported_modalities: List[str]
    phase_introduced: int
    is_active: bool = False


class ToolRegistry:
    """
    Catalog of remote-sensing analysis tools accessible to the agentic orchestrator.
    Phase 1 establishes metadata schema and tool definitions; execution implementations
    are wired in Phases 2-6.
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._executors: Dict[str, Callable[..., Any]] = {}
        self._register_default_catalog()

    def _register_default_catalog(self):
        """Define the master SIH Problem 26167 remote sensing tool specifications."""
        tools = [
            ToolMetadata(
                name="single_vqa",
                description="Visual Question Answering on single optical/multispectral satellite imagery.",
                required_inputs=["image_id", "question"],
                supported_modalities=["optical", "multispectral"],
                phase_introduced=2,
                is_active=False
            ),
            ToolMetadata(
                name="caption",
                description="Detailed technical scene description and land-use categorization.",
                required_inputs=["image_id"],
                supported_modalities=["optical", "multispectral", "sar"],
                phase_introduced=2,
                is_active=False
            ),
            ToolMetadata(
                name="grounding",
                description="Spatial localization of natural language expressions into bounding boxes/coordinates.",
                required_inputs=["image_id", "query"],
                supported_modalities=["optical", "multispectral"],
                phase_introduced=4,
                is_active=False
            ),
            ToolMetadata(
                name="change_detection",
                description="Pixel-level and semantic bi-temporal change detection across two timestamps.",
                required_inputs=["before_image_id", "after_image_id"],
                supported_modalities=["optical", "sar"],
                phase_introduced=5,
                is_active=False
            ),
            ToolMetadata(
                name="change_vqa",
                description="Natural language question answering concerning differences across bi-temporal pairs.",
                required_inputs=["before_image_id", "after_image_id", "question"],
                supported_modalities=["optical", "sar"],
                phase_introduced=5,
                is_active=False
            ),
            ToolMetadata(
                name="optical_sar_analysis",
                description="Fused multimodal analysis across co-registered optical and Synthetic Aperture Radar (SAR) pairs.",
                required_inputs=["optical_image_id", "sar_image_id", "query"],
                supported_modalities=["optical", "sar"],
                phase_introduced=6,
                is_active=False
            ),
        ]
        for t in tools:
            self._tools[t.name] = t

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolMetadata]:
        return list(self._tools.values())

    def register_executor(self, name: str, executor: Callable[..., Any]):
        """Attach an active inference callable to a tool (Phase 2+)."""
        if name not in self._tools:
            raise KeyError(f"Tool {name} is not defined in the catalog.")
        self._executors[name] = executor
        self._tools[name].is_active = True
