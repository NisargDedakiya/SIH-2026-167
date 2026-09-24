"""
Spatial Overlap and Compatibility Analyzer for Optical-SAR Image Pairs.
Evaluates CRS, geospatial bounding boxes, spatial resolution, and calculates
intersection area and overlap ratio without assuming same dimensions equals alignment.
"""

from typing import Any, Dict, Optional, Tuple
from rasterio.crs import CRS
from rasterio.warp import transform_bounds

from app.core.logging import logger
from app.cross_modal.models import (
    COMPATIBILITY_COMPATIBLE,
    COMPATIBILITY_INCOMPATIBLE,
    COMPATIBILITY_INSUFFICIENT_METADATA,
    COMPATIBILITY_PARTIALLY_COMPATIBLE,
)
from app.database.models import ImageModel


class CrossModalSpatialCompatibility:
    """
    Evaluates spatial compatibility and computes geospatial intersection between
    an Optical and a SAR raster.
    """

    MIN_OVERLAP_FOR_COMPATIBLE: float = 0.50
    MIN_OVERLAP_FOR_PARTIAL: float = 0.05

    @classmethod
    def evaluate(
        cls,
        optical_image: ImageModel,
        sar_image: ImageModel,
    ) -> Dict[str, Any]:
        """
        Compares spatial specifications and calculates overlap ratio.
        Returns:
            {
                "compatibility": "COMPATIBLE" | "PARTIALLY_COMPATIBLE" | "INCOMPATIBLE" | "INSUFFICIENT_METADATA",
                "is_compatible": bool,
                "overlap_ratio": float,
                "optical_overlap": float,
                "sar_overlap": float,
                "needs_reprojection": bool,
                "needs_resampling": bool,
                "intersection_bounds": Optional[Dict[str, float]],
                "message": str,
                "details": Dict[str, Any]
            }
        """
        # Case 1: Both images lack geospatial CRS / referencing
        if not optical_image.is_geospatial and not sar_image.is_geospatial:
            dim_ratio_w = min(optical_image.width, sar_image.width) / max(optical_image.width, sar_image.width)
            dim_ratio_h = min(optical_image.height, sar_image.height) / max(optical_image.height, sar_image.height)
            pixel_ratio = round(dim_ratio_w * dim_ratio_h, 4)

            if pixel_ratio >= cls.MIN_OVERLAP_FOR_COMPATIBLE:
                compat = COMPATIBILITY_COMPATIBLE
            elif pixel_ratio >= cls.MIN_OVERLAP_FOR_PARTIAL:
                compat = COMPATIBILITY_PARTIALLY_COMPATIBLE
            else:
                compat = COMPATIBILITY_INCOMPATIBLE

            return {
                "compatibility": compat,
                "is_compatible": compat in (COMPATIBILITY_COMPATIBLE, COMPATIBILITY_PARTIALLY_COMPATIBLE),
                "overlap_ratio": pixel_ratio,
                "optical_overlap": pixel_ratio,
                "sar_overlap": pixel_ratio,
                "needs_reprojection": False,
                "needs_resampling": optical_image.width != sar_image.width or optical_image.height != sar_image.height,
                "intersection_bounds": None,
                "message": "Both images lack geospatial referencing; evaluated based on raster pixel geometry.",
                "details": {
                    "optical_dims": f"{optical_image.width}x{optical_image.height}",
                    "sar_dims": f"{sar_image.width}x{sar_image.height}",
                    "is_geospatial": False,
                }
            }

        # Case 2: One is georeferenced but the other is not
        if optical_image.is_geospatial != sar_image.is_geospatial:
            return {
                "compatibility": COMPATIBILITY_INSUFFICIENT_METADATA,
                "is_compatible": False,
                "overlap_ratio": 0.0,
                "optical_overlap": 0.0,
                "sar_overlap": 0.0,
                "needs_reprojection": False,
                "needs_resampling": False,
                "intersection_bounds": None,
                "message": "One image contains geospatial reference metadata while the other lacks geospatial referencing.",
                "details": {
                    "optical_is_geospatial": optical_image.is_geospatial,
                    "sar_is_geospatial": sar_image.is_geospatial,
                }
            }

        # Case 3: Both images are georeferenced
        bounds_opt = optical_image.bounds or {}
        bounds_sar = sar_image.bounds or {}

        if not bounds_opt or not bounds_sar:
            return {
                "compatibility": COMPATIBILITY_INSUFFICIENT_METADATA,
                "is_compatible": False,
                "overlap_ratio": 0.0,
                "optical_overlap": 0.0,
                "sar_overlap": 0.0,
                "needs_reprojection": False,
                "needs_resampling": False,
                "intersection_bounds": None,
                "message": "Missing bounding coordinates in one or both geospatial records.",
                "details": {
                    "optical_bounds_present": bool(bounds_opt),
                    "sar_bounds_present": bool(bounds_sar),
                }
            }

        try:
            crs_opt = CRS.from_user_input(optical_image.crs) if optical_image.crs else None
            crs_sar = CRS.from_user_input(sar_image.crs) if sar_image.crs else None
        except Exception as e:
            logger.warning(f"CRS parsing error in cross-modal compatibility: {e}")
            crs_opt, crs_sar = None, None

        if not crs_opt or not crs_sar:
            return {
                "compatibility": COMPATIBILITY_INSUFFICIENT_METADATA,
                "is_compatible": False,
                "overlap_ratio": 0.0,
                "optical_overlap": 0.0,
                "sar_overlap": 0.0,
                "needs_reprojection": False,
                "needs_resampling": False,
                "intersection_bounds": None,
                "message": "Could not parse CRS definition for optical or SAR image.",
                "details": {
                    "optical_crs": optical_image.crs,
                    "sar_crs": sar_image.crs,
                }
            }

        needs_reprojection = crs_opt != crs_sar

        # Transform SAR bounds into Optical CRS frame if CRS differs
        if needs_reprojection:
            try:
                sar_left = bounds_sar.get("left", bounds_sar.get("west", 0.0))
                sar_bottom = bounds_sar.get("bottom", bounds_sar.get("south", 0.0))
                sar_right = bounds_sar.get("right", bounds_sar.get("east", 0.0))
                sar_top = bounds_sar.get("top", bounds_sar.get("north", 0.0))

                t_left, t_bottom, t_right, t_top = transform_bounds(
                    src_crs=crs_sar,
                    dst_crs=crs_opt,
                    left=sar_left,
                    bottom=sar_bottom,
                    right=sar_right,
                    top=sar_top
                )
                sar_comp_bounds = {
                    "left": t_left,
                    "bottom": t_bottom,
                    "right": t_right,
                    "top": t_top,
                }
            except Exception as e:
                logger.error(f"Failed to transform SAR bounds to Optical CRS: {e}")
                return {
                    "compatibility": COMPATIBILITY_INCOMPATIBLE,
                    "is_compatible": False,
                    "overlap_ratio": 0.0,
                    "optical_overlap": 0.0,
                    "sar_overlap": 0.0,
                    "needs_reprojection": True,
                    "needs_resampling": True,
                    "intersection_bounds": None,
                    "message": f"CRS transformation between optical and SAR failed: {str(e)}",
                    "details": {"error": str(e)}
                }
        else:
            sar_comp_bounds = bounds_sar

        opt_left = bounds_opt.get("left", bounds_opt.get("west", 0.0))
        opt_bottom = bounds_opt.get("bottom", bounds_opt.get("south", 0.0))
        opt_right = bounds_opt.get("right", bounds_opt.get("east", 0.0))
        opt_top = bounds_opt.get("top", bounds_opt.get("north", 0.0))

        s_left = sar_comp_bounds.get("left", sar_comp_bounds.get("west", 0.0))
        s_bottom = sar_comp_bounds.get("bottom", sar_comp_bounds.get("south", 0.0))
        s_right = sar_comp_bounds.get("right", sar_comp_bounds.get("east", 0.0))
        s_top = sar_comp_bounds.get("top", sar_comp_bounds.get("north", 0.0))

        # Calculate bounding box intersection
        int_left = max(opt_left, s_left)
        int_bottom = max(opt_bottom, s_bottom)
        int_right = min(opt_right, s_right)
        int_top = min(opt_top, s_top)

        if int_right <= int_left or int_top <= int_bottom:
            return {
                "compatibility": COMPATIBILITY_INCOMPATIBLE,
                "is_compatible": False,
                "overlap_ratio": 0.0,
                "optical_overlap": 0.0,
                "sar_overlap": 0.0,
                "needs_reprojection": needs_reprojection,
                "needs_resampling": True,
                "intersection_bounds": None,
                "message": "No spatial overlap found between the Optical and SAR scenes.",
                "details": {
                    "optical_bounds": bounds_opt,
                    "sar_bounds_projected": sar_comp_bounds,
                }
            }

        intersection_area = (int_right - int_left) * (int_top - int_bottom)
        opt_area = max(1e-9, (opt_right - opt_left) * (opt_top - opt_bottom))
        sar_area = max(1e-9, (s_right - s_left) * (s_top - s_bottom))

        opt_overlap = round(min(1.0, intersection_area / opt_area), 4)
        sar_overlap = round(min(1.0, intersection_area / sar_area), 4)
        overlap_ratio = round(min(opt_overlap, sar_overlap), 4)

        needs_resampling = (
            optical_image.width != sar_image.width
            or optical_image.height != sar_image.height
            or (optical_image.resolution_x and sar_image.resolution_x and abs(optical_image.resolution_x - sar_image.resolution_x) > 1e-4)
        )

        if overlap_ratio >= cls.MIN_OVERLAP_FOR_COMPATIBLE:
            compat = COMPATIBILITY_COMPATIBLE
            msg = f"Optical and SAR images exhibit high spatial overlap ({round(overlap_ratio * 100, 1)}%)."
        elif overlap_ratio >= cls.MIN_OVERLAP_FOR_PARTIAL:
            compat = COMPATIBILITY_PARTIALLY_COMPATIBLE
            msg = f"Optical and SAR images exhibit partial spatial overlap ({round(overlap_ratio * 100, 1)}%)."
        else:
            compat = COMPATIBILITY_INCOMPATIBLE
            msg = f"Spatial overlap is below minimum threshold ({round(overlap_ratio * 100, 1)}%)."

        return {
            "compatibility": compat,
            "is_compatible": compat in (COMPATIBILITY_COMPATIBLE, COMPATIBILITY_PARTIALLY_COMPATIBLE),
            "overlap_ratio": overlap_ratio,
            "optical_overlap": opt_overlap,
            "sar_overlap": sar_overlap,
            "needs_reprojection": needs_reprojection,
            "needs_resampling": needs_resampling,
            "intersection_bounds": {
                "left": int_left,
                "bottom": int_bottom,
                "right": int_right,
                "top": int_top,
                "crs": str(crs_opt),
            },
            "message": msg,
            "details": {
                "optical_crs": str(crs_opt),
                "sar_crs": str(crs_sar),
                "optical_res": optical_image.resolution_x,
                "sar_res": sar_image.resolution_x,
                "needs_reprojection": needs_reprojection,
                "needs_resampling": needs_resampling,
            }
        }
