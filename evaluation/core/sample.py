"""
Common benchmark sample schema for SatQuery AI.
Normalized representation of multimodal remote-sensing evaluation items.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from PIL import Image


@dataclass
class BenchmarkSample:
    """
    Standard evaluation sample schema.
    Accommodates single-image, bi-temporal, optical-SAR, and routing tasks.
    """
    sample_id: str
    task: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    query: Optional[str] = None
    reference: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def primary_image(self) -> Optional[Image.Image]:
        return self.inputs.get("image") or self.inputs.get("optical")

    @property
    def t1_image(self) -> Optional[Image.Image]:
        return self.inputs.get("image_t1")

    @property
    def t2_image(self) -> Optional[Image.Image]:
        return self.inputs.get("image_t2")

    @property
    def sar_image(self) -> Optional[Image.Image]:
        return self.inputs.get("sar")

    @property
    def ground_truth_answer(self) -> Optional[str]:
        return self.reference.get("answer")

    @property
    def ground_truth_caption(self) -> Optional[str]:
        return self.reference.get("caption")

    @property
    def ground_truth_regions(self) -> List[Dict[str, Any]]:
        return self.reference.get("regions", [])

    @property
    def ground_truth_change_mask(self) -> Optional[Any]:
        return self.reference.get("change_mask")
