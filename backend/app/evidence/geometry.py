"""
Coordinate & Geometry Transformations for Remote-Sensing Grounding.
Maps bounding boxes between model input space, raw original raster pixel space,
and native geospatial Coordinate Reference Systems (CRS).
"""

from typing import Any, Dict, List, Optional, Tuple
import rasterio.transform


def rescale_normalized_to_pixel(
    norm_bbox: List[float],
    orig_width: int,
    orig_height: int
) -> Dict[str, int]:
    """
    Converts normalized [x1, y1, x2, y2] coordinates (range 0.0 to 1.0)
    to original raster pixel coordinates {x1, y1, x2, y2, width, height}.
    Clamps bounds within the image boundary.
    """
    x1, y1, x2, y2 = norm_bbox
    x1_px = max(0, min(orig_width - 1, int(round(x1 * orig_width))))
    y1_px = max(0, min(orig_height - 1, int(round(y1 * orig_height))))
    x2_px = max(x1_px + 1, min(orig_width, int(round(x2 * orig_width))))
    y2_px = max(y1_px + 1, min(orig_height, int(round(y2 * orig_height))))

    return {
        "x1": x1_px,
        "y1": y1_px,
        "x2": x2_px,
        "y2": y2_px,
        "width": x2_px - x1_px,
        "height": y2_px - y1_px,
    }


def pixel_bbox_to_geo_bounds(
    pixel_bbox: Dict[str, int],
    transform: Optional[Any],
    crs: Optional[str]
) -> Optional[Dict[str, Any]]:
    """
    Reprojects pixel bounding box coordinates into real-world coordinates
    using the raster's affine geotransform and native CRS.
    Returns None if the image lacks geospatial referencing.
    """
    if not crs or not transform:
        return None

    try:
        # Convert transform list to Affine if needed
        if isinstance(transform, list):
            aff = rasterio.transform.Affine(*transform[:6])
        elif isinstance(transform, dict):
            aff = rasterio.transform.Affine(
                transform.get("a", 1.0),
                transform.get("b", 0.0),
                transform.get("c", 0.0),
                transform.get("d", 0.0),
                transform.get("e", -1.0),
                transform.get("f", 0.0),
            )
        else:
            aff = transform

        x1 = pixel_bbox["x1"]
        y1 = pixel_bbox["y1"]
        x2 = pixel_bbox["x2"]
        y2 = pixel_bbox["y2"]

        # rasterio.transform.xy(transform, row, col, offset='ul') -> corner (x_coord, y_coord)
        x_min, y_max = rasterio.transform.xy(aff, y1, x1, offset="ul")
        x_max, y_min = rasterio.transform.xy(aff, y2, x2, offset="ul")

        # Polygon coordinates in native CRS (counter-clockwise: top-left, bottom-left, bottom-right, top-right, closed)
        polygon = [
            [round(x_min, 6), round(y_max, 6)],
            [round(x_min, 6), round(y_min, 6)],
            [round(x_max, 6), round(y_min, 6)],
            [round(x_max, 6), round(y_max, 6)],
            [round(x_min, 6), round(y_max, 6)],
        ]

        return {
            "crs": crs,
            "bounds": {
                "min_x": round(min(x_min, x_max), 6),
                "min_y": round(min(y_min, y_max), 6),
                "max_x": round(max(x_min, x_max), 6),
                "max_y": round(max(y_min, y_max), 6),
            },
            "polygon": polygon,
            "formatted": f"CRS: {crs} | [{min(x_min, x_max):.2f}, {min(y_min, y_max):.2f}] to [{max(x_min, x_max):.2f}, {max(y_min, y_max):.2f}]"
        }
    except Exception:
        return None
