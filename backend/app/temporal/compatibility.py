"""
Spatial Overlap and Compatibility Analyzer.
Evaluates geospatial bounds, Coordinate Reference Systems (CRS), resolution,
and calculates intersection areas and overlap ratios between T1 and T2 rasters.
"""

from typing import Any, Dict, Optional, Tuple
from rasterio.crs import CRS
from rasterio.warp import transform_bounds

from app.core.logging import logger
from app.database.models import ImageModel


class SpatialCompatibilityChecker:
    """
    Evaluates spatial compatibility and calculates bounding box overlap between two remote-sensing rasters.
    """

    MIN_OVERLAP_THRESHOLD: float = 0.10  # 10% minimum overlap required

    @classmethod
    def check_spatial_compatibility(
        cls,
        image_t1: ImageModel,
        image_t2: ImageModel,
        min_overlap: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates spatial overlap and determines compatibility status.
        Returns:
            {
                "compatible": bool,
                "status_code": "SPATIALLY_COMPATIBLE" | "SPATIAL_MISMATCH" | "INSUFFICIENT_GEOSPATIAL_METADATA" | "CRS_MISMATCH",
                "overlap_ratio_t1": float,
                "overlap_ratio_t2": float,
                "overlap_ratio": float,
                "needs_reprojection": bool,
                "needs_resampling": bool,
                "message": str,
                "details": {...}
            }
        """
        threshold = min_overlap if min_overlap is not None else cls.MIN_OVERLAP_THRESHOLD

        # Case 1: Both images lack geospatial CRS / referencing
        if not image_t1.is_geospatial and not image_t2.is_geospatial:
            # Fall back to pixel dimension comparability
            dim_ratio_w = min(image_t1.width, image_t2.width) / max(image_t1.width, image_t2.width)
            dim_ratio_h = min(image_t1.height, image_t2.height) / max(image_t1.height, image_t2.height)
            pixel_compat = dim_ratio_w >= 0.5 and dim_ratio_h >= 0.5

            return {
                "compatible": pixel_compat,
                "status_code": "SPATIALLY_COMPATIBLE" if pixel_compat else "SPATIAL_MISMATCH",
                "overlap_ratio_t1": round(dim_ratio_w * dim_ratio_h, 4),
                "overlap_ratio_t2": round(dim_ratio_w * dim_ratio_h, 4),
                "overlap_ratio": round(dim_ratio_w * dim_ratio_h, 4),
                "needs_reprojection": False,
                "needs_resampling": image_t1.width != image_t2.width or image_t1.height != image_t2.height,
                "message": (
                    "Images lack geospatial referencing; spatial compatibility evaluated via pixel raster geometry."
                    if pixel_compat
                    else "Pixel dimensions diverge significantly between T1 and T2."
                ),
                "details": {
                    "t1_dims": f"{image_t1.width}x{image_t1.height}",
                    "t2_dims": f"{image_t2.width}x{image_t2.height}",
                    "geospatial": False,
                }
            }

        # Case 2: One is georeferenced but the other is not
        if image_t1.is_geospatial != image_t2.is_geospatial:
            return {
                "compatible": False,
                "status_code": "INSUFFICIENT_GEOSPATIAL_METADATA",
                "overlap_ratio_t1": 0.0,
                "overlap_ratio_t2": 0.0,
                "overlap_ratio": 0.0,
                "needs_reprojection": False,
                "needs_resampling": False,
                "message": "One image contains geospatial reference metadata while the other is an unreferenced raster.",
                "details": {
                    "t1_is_geospatial": image_t1.is_geospatial,
                    "t2_is_geospatial": image_t2.is_geospatial,
                }
            }

        # Case 3: Both images are georeferenced
        bounds_t1 = image_t1.bounds or {}
        bounds_t2 = image_t2.bounds or {}

        if not bounds_t1 or not bounds_t2:
            return {
                "compatible": False,
                "status_code": "INSUFFICIENT_GEOSPATIAL_METADATA",
                "overlap_ratio_t1": 0.0,
                "overlap_ratio_t2": 0.0,
                "overlap_ratio": 0.0,
                "needs_reprojection": False,
                "needs_resampling": False,
                "message": "Geospatial bounding coordinates missing from image metadata.",
                "details": {}
            }

        crs_t1_str = image_t1.crs
        crs_t2_str = image_t2.crs

        needs_reprojection = False
        t2_left = bounds_t2.get("left", 0.0)
        t2_bottom = bounds_t2.get("bottom", 0.0)
        t2_right = bounds_t2.get("right", 0.0)
        t2_top = bounds_t2.get("top", 0.0)

        # Reproject T2 bounds to T1's CRS if CRS differs
        if crs_t1_str and crs_t2_str and crs_t1_str != crs_t2_str:
            needs_reprojection = True
            try:
                crs_1 = CRS.from_user_input(crs_t1_str)
                crs_2 = CRS.from_user_input(crs_t2_str)
                t2_left, t2_bottom, t2_right, t2_top = transform_bounds(
                    crs_2, crs_1, t2_left, t2_bottom, t2_right, t2_top
                )
            except Exception as e:
                logger.warning(f"Failed to transform bounds between {crs_t2_str} and {crs_t1_str}: {e}")
                return {
                    "compatible": False,
                    "status_code": "CRS_MISMATCH",
                    "overlap_ratio_t1": 0.0,
                    "overlap_ratio_t2": 0.0,
                    "overlap_ratio": 0.0,
                    "needs_reprojection": True,
                    "needs_resampling": False,
                    "message": f"Incompatible Coordinate Reference Systems: {crs_t1_str} vs {crs_t2_str}.",
                    "details": {"crs_t1": crs_t1_str, "crs_t2": crs_t2_str}
                }

        t1_left = bounds_t1.get("left", 0.0)
        t1_bottom = bounds_t1.get("bottom", 0.0)
        t1_right = bounds_t1.get("right", 0.0)
        t1_top = bounds_t1.get("top", 0.0)

        # Calculate 2D Axis-Aligned Bounding Box Intersection
        inter_left = max(t1_left, t2_left)
        inter_bottom = max(t1_bottom, t2_bottom)
        inter_right = min(t1_right, t2_right)
        inter_top = min(t1_top, t2_top)

        inter_width = max(0.0, inter_right - inter_left)
        inter_height = max(0.0, inter_top - inter_bottom)
        inter_area = inter_width * inter_height

        area_t1 = max(1e-9, (t1_right - t1_left) * (t1_top - t1_bottom))
        area_t2 = max(1e-9, (t2_right - t2_left) * (t2_top - t2_bottom))

        overlap_t1 = min(1.0, max(0.0, inter_area / area_t1))
        overlap_t2 = min(1.0, max(0.0, inter_area / area_t2))
        combined_overlap = min(overlap_t1, overlap_t2)

        res1_x = getattr(image_t1, "resolution_x", None)
        res2_x = getattr(image_t2, "resolution_x", None)
        res_x_match = (
            res1_x is not None
            and res2_x is not None
            and abs(res1_x - res2_x) < 1e-4
        )
        needs_resampling = not res_x_match or image_t1.width != image_t2.width or image_t1.height != image_t2.height

        is_compatible = combined_overlap >= threshold

        return {
            "compatible": is_compatible,
            "status_code": "SPATIALLY_COMPATIBLE" if is_compatible else "SPATIAL_MISMATCH",
            "overlap_ratio_t1": round(overlap_t1, 4),
            "overlap_ratio_t2": round(overlap_t2, 4),
            "overlap_ratio": round(combined_overlap, 4),
            "needs_reprojection": needs_reprojection,
            "needs_resampling": needs_resampling,
            "message": (
                f"Spatially compatible with {combined_overlap * 100:.1f}% geographic overlap."
                if is_compatible
                else f"Insufficient spatial overlap: {combined_overlap * 100:.1f}% (required >= {threshold * 100:.0f}%)."
            ),
            "details": {
                "crs_t1": crs_t1_str,
                "crs_t2": crs_t2_str,
                "intersection_bounds": {
                    "left": round(inter_left, 4),
                    "bottom": round(inter_bottom, 4),
                    "right": round(inter_right, 4),
                    "top": round(inter_top, 4),
                },
                "area_overlap_pct": round(combined_overlap * 100, 2),
            }
        }
