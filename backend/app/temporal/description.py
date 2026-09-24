"""
Natural Language Change Description Engine.
Transforms structured change metrics, spatial quadrants, and region geometries
into concise, evidence-grounded natural-language descriptions.
"""

from typing import Any, Dict, List, Optional
from app.temporal.change_map import ChangeMap
from app.temporal.schemas import ChangeRegion


class ChangeDescriptionEngine:
    """
    Synthesizes factual change summaries grounded in spatial measurements and detected regions.
    """

    @classmethod
    def generate_description(
        cls,
        change_map: ChangeMap,
        regions: List[ChangeRegion],
        query: Optional[str] = None
    ) -> str:
        """
        Produces a grounded textual description of bi-temporal changes.
        """
        if not change_map.has_change or len(regions) == 0:
            return "No significant structural or land-cover changes were detected between the two acquisition dates within the verified spatial overlap."

        pct = change_map.change_percentage
        reg_count = len(regions)
        q = (query or "").lower()

        # Spatial quadrant distribution
        quadrants = cls._analyze_spatial_distribution(regions, change_map.width, change_map.height)
        quad_phrase = f"concentrated primarily in the {', '.join(quadrants)}" if quadrants else "distributed across the scene"

        # Check for specific target semantics in user query
        if "construction" in q or "building" in q or "structure" in q:
            return (
                f"Bi-temporal analysis detected {reg_count} changed region{'s' if reg_count > 1 else ''} "
                f"accounting for {pct:.1f}% of the scene area, {quad_phrase}. "
                f"The spatial signatures indicate newly modified built-up structures and ground alterations."
            )
        elif "vegetation" in q or "forest" in q or "agriculture" in q:
            return (
                f"Detected {reg_count} significant vegetative change zone{'s' if reg_count > 1 else ''} "
                f"covering {pct:.1f}% of the observed area, {quad_phrase}."
            )
        elif "water" in q or "river" in q or "lake" in q or "flood" in q:
            return (
                f"Hydrological analysis detected {reg_count} changed region{'s' if reg_count > 1 else ''} "
                f"amounting to {pct:.1f}% surface area variation, {quad_phrase}."
            )
        elif "road" in q or "transport" in q:
            return (
                f"Infrastructure inspection identified {reg_count} altered corridor segment{'s' if reg_count > 1 else ''} "
                f"spanning {pct:.1f}% of the analyzed scene, {quad_phrase}."
            )

        # General change description
        return (
            f"Bi-temporal change analysis detected {reg_count} distinct changed region{'s' if reg_count > 1 else ''} "
            f"spanning {pct:.1f}% of the scene area ({change_map.changed_pixels:,} pixels), {quad_phrase}."
        )

    @classmethod
    def _analyze_spatial_distribution(cls, regions: List[ChangeRegion], width: int, height: int) -> List[str]:
        """Categorizes where the bulk of the changes occur (north, south, east, west, center)."""
        if not regions:
            return []

        counts = {"northern": 0, "southern": 0, "eastern": 0, "western": 0, "central": 0}

        for r in regions:
            mid_x = (r.pixel_geometry["x1"] + r.pixel_geometry["x2"]) / 2.0
            mid_y = (r.pixel_geometry["y1"] + r.pixel_geometry["y2"]) / 2.0

            # Normalized position
            norm_x = mid_x / max(1, width)
            norm_y = mid_y / max(1, height)

            if 0.35 <= norm_x <= 0.65 and 0.35 <= norm_y <= 0.65:
                counts["central"] += 1
            else:
                if norm_y < 0.45:
                    counts["northern"] += 1
                elif norm_y > 0.55:
                    counts["southern"] += 1

                if norm_x < 0.45:
                    counts["western"] += 1
                elif norm_x > 0.55:
                    counts["eastern"] += 1

        active = [quad for quad, count in counts.items() if count >= max(1, len(regions) // 3)]
        return active[:2]
