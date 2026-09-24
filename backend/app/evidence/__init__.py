"""
Visual Evidence Engine package.
"""

from app.evidence.geometry import pixel_bbox_to_geo_bounds, rescale_normalized_to_pixel
from app.evidence.overlay import render_evidence_overlay, render_region_crop
from app.evidence.renderer import process_grounding_evidence

__all__ = [
    "rescale_normalized_to_pixel",
    "pixel_bbox_to_geo_bounds",
    "render_evidence_overlay",
    "render_region_crop",
    "process_grounding_evidence",
]
