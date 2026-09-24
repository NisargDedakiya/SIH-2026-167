"""
Change Region Extraction and Geospatial Geometry Engine.
Applies morphological cleanup, connected component extraction via rasterio.features,
small-region filtering, and projects pixel bounding boxes to native geospatial CRS coordinates.
"""

import uuid
from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image, ImageFilter
import rasterio.features

from app.evidence.geometry import pixel_bbox_to_geo_bounds
from app.temporal.change_map import ChangeMap
from app.temporal.schemas import ChangeRegion


class ChangeRegionExtractor:
    """
    Converts 2D spatial change maps into discrete, semantically identifiable change regions
    with pixel coordinates, normalized bounds, and native geospatial CRS geometry.
    """

    @classmethod
    def extract_regions(
        cls,
        change_map: ChangeMap,
        transform: Optional[Any] = None,
        crs: Optional[str] = None,
        min_region_size: int = 25,
        max_regions: int = 20,
        default_label: str = "detected change region"
    ) -> List[ChangeRegion]:
        """
        Extracts bounded change regions from the binary change mask.
        """
        mask = change_map.mask
        h, w = mask.shape

        if np.sum(mask) == 0:
            return []

        # 1. Morphological cleanup: remove speckle noise (opening) and bridge micro-gaps (closing)
        mask_u8 = (mask * 255).astype(np.uint8)
        pil_img = Image.fromarray(mask_u8)

        # Opening (Min then Max)
        opened = pil_img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
        # Closing (Max then Min)
        closed = opened.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))

        cleaned_arr = (np.array(closed) > 127).astype(np.uint8)

        # If morphological opening removed all features, preserve raw mask
        if np.sum(cleaned_arr) == 0:
            cleaned_arr = mask.astype(np.uint8)

        # 2. Connected Component Polygon Extraction via rasterio.features
        shapes_gen = rasterio.features.shapes(
            cleaned_arr.astype(np.int16),
            mask=(cleaned_arr > 0),
            connectivity=8
        )

        regions_data: List[Dict[str, Any]] = []
        total_pixels = h * w

        for geom, val in shapes_gen:
            if val == 0:
                continue

            coords = geom.get("coordinates", [])
            if not coords or not coords[0]:
                continue

            poly_pts = coords[0]
            x_pts = [p[0] for p in poly_pts]
            y_pts = [p[1] for p in poly_pts]

            x1 = max(0, min(w - 1, int(np.floor(min(x_pts)))))
            y1 = max(0, min(h - 1, int(np.floor(min(y_pts)))))
            x2 = max(x1 + 1, min(w, int(np.ceil(max(x_pts)))))
            y2 = max(y1 + 1, min(h, int(np.ceil(max(y_pts)))))

            region_submask = cleaned_arr[y1:y2, x1:x2]
            pixel_count = int(np.sum(region_submask))

            if pixel_count < min_region_size:
                continue

            region_scores = change_map.scores[y1:y2, x1:x2][region_submask > 0]
            conf = float(np.mean(region_scores)) if len(region_scores) > 0 else 0.85

            regions_data.append({
                "pixel_count": pixel_count,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "confidence": round(conf, 4)
            })

        # Sort regions by size descending and take top max_regions
        regions_data.sort(key=lambda r: r["pixel_count"], reverse=True)
        top_regions = regions_data[:max_regions]

        # 3. Standardize into ChangeRegion models
        extracted: List[ChangeRegion] = []

        for idx, r in enumerate(top_regions):
            px_x1 = r["x1"]
            px_y1 = r["y1"]
            px_x2 = r["x2"]
            px_y2 = r["y2"]
            px_w = px_x2 - px_x1
            px_h = px_y2 - px_y1

            pixel_geo = {
                "x1": px_x1,
                "y1": px_y1,
                "x2": px_x2,
                "y2": px_y2,
                "width": px_w,
                "height": px_h,
            }

            norm_bbox = [
                round(px_x1 / w, 4),
                round(px_y1 / h, 4),
                round(px_x2 / w, 4),
                round(px_y2 / h, 4),
            ]

            # Native CRS geospatial reprojection
            geo_geo = pixel_bbox_to_geo_bounds(
                pixel_bbox=pixel_geo,
                transform=transform,
                crs=crs
            )

            reg = ChangeRegion(
                region_id=f"change_region_{idx + 1}",
                label=f"{default_label} #{idx + 1}",
                confidence=r["confidence"],
                bbox=norm_bbox,
                pixel_geometry=pixel_geo,
                geo_geometry=geo_geo,
                pixel_area=r["pixel_count"],
                relative_area=round(r["pixel_count"] / total_pixels, 6),
            )
            extracted.append(reg)

        return extracted
