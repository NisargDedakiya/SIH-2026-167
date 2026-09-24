"""
Artifact Storage Management for Visual Evidence.
Uploads generated visual overlays and region crops to the SatQuery object store.
"""

import uuid
from typing import Any, Dict, List, Optional
from PIL import Image

from app.core.logging import logger
from app.evidence.overlay import image_to_png_bytes, render_evidence_overlay, render_region_crop
from app.storage.object_store import ObjectStore, get_object_store


async def persist_evidence_artifacts(
    base_image: Image.Image,
    regions: List[Dict[str, Any]],
    analysis_id: uuid.UUID,
    store: Optional[ObjectStore] = None
) -> Dict[str, Any]:
    """
    Generates and stores the complete visual overlay artifact as well as
    individual high-resolution region crop thumbnails.
    Returns mapping of artifact keys.
    """
    storage = store or get_object_store()
    artifacts_map: Dict[str, Any] = {
        "overlay_key": None,
        "crop_keys": []
    }

    if not regions:
        return artifacts_map

    try:
        # 1. Generate & persist full visual overlay
        overlay_img = render_evidence_overlay(base_image, regions)
        overlay_bytes = image_to_png_bytes(overlay_img)
        overlay_key = f"evidence/{analysis_id}/overlay.png"

        await storage.upload_bytes(
            key=overlay_key,
            data=overlay_bytes,
            content_type="image/png"
        )
        artifacts_map["overlay_key"] = overlay_key

        # 2. Generate & persist crop for each detected region
        for idx, region in enumerate(regions):
            pixel_geo = region.get("pixel_geometry", {})
            if pixel_geo and pixel_geo.get("width", 0) > 0 and pixel_geo.get("height", 0) > 0:
                crop_img = render_region_crop(base_image, pixel_geo)
                crop_bytes = image_to_png_bytes(crop_img)
                crop_key = f"evidence/{analysis_id}/crop_{idx}.png"

                await storage.upload_bytes(
                    key=crop_key,
                    data=crop_bytes,
                    content_type="image/png"
                )
                region["crop_artifact_key"] = crop_key
                artifacts_map["crop_keys"].append(crop_key)

    except Exception as e:
        logger.error(f"Failed to persist visual evidence artifacts for analysis '{analysis_id}': {e}", exc_info=True)

    return artifacts_map
