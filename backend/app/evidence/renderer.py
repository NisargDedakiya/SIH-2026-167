"""
Evidence Orchestration and Generation Engine.
Coordinates geometry projection, CRS mapping, artifact rendering, and database persistence.
"""

import io
import uuid
from typing import Any, Dict, List, Optional
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.preprocessing import RemoteSensingPreprocessor
from app.core.logging import logger
from app.database.models import EvidenceModel, ImageModel
from app.evidence.artifacts import persist_evidence_artifacts
from app.evidence.geometry import pixel_bbox_to_geo_bounds, rescale_normalized_to_pixel


async def process_grounding_evidence(
    raw_regions: List[Dict[str, Any]],
    image_record: ImageModel,
    image_bytes: bytes,
    analysis_id: uuid.UUID,
    db: Optional[AsyncSession] = None
) -> List[Dict[str, Any]]:
    """
    Transforms raw model region detections into standardized, persistent visual evidence records.
    Renders overlays, reprojects CRS bounds, and commits records to SQLite.
    """
    orig_w = image_record.width
    orig_h = image_record.height

    processed_regions: List[Dict[str, Any]] = []

    # 1. Map coordinates
    for reg in raw_regions:
        label = reg.get("label", "detected_region")
        conf = float(reg.get("confidence", 0.85))

        # Check if model provided normalized [0..1] or pixel coordinates
        if "bbox" in reg:
            raw_box = reg["bbox"]
            if all(0.0 <= val <= 1.0 for val in raw_box):
                norm_box = raw_box
                pixel_geo = rescale_normalized_to_pixel(norm_box, orig_w, orig_h)
            else:
                # Already in pixels
                x1, y1, x2, y2 = [int(v) for v in raw_box]
                pixel_geo = {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "width": x2 - x1,
                    "height": y2 - y1
                }
                norm_box = [
                    round(x1 / orig_w, 4),
                    round(y1 / orig_h, 4),
                    round(x2 / orig_w, 4),
                    round(y2 / orig_h, 4)
                ]
        elif "pixel_geometry" in reg:
            pixel_geo = reg["pixel_geometry"]
            norm_box = [
                round(pixel_geo["x1"] / orig_w, 4),
                round(pixel_geo["y1"] / orig_h, 4),
                round(pixel_geo["x2"] / orig_w, 4),
                round(pixel_geo["y2"] / orig_h, 4)
            ]
        else:
            continue

        # Geospatial bounds
        geo_geo = pixel_bbox_to_geo_bounds(
            pixel_bbox=pixel_geo,
            transform=image_record.transform,
            crs=image_record.crs
        )

        evidence_entry = {
            "id": str(uuid.uuid4()),
            "analysis_id": str(analysis_id),
            "image_id": str(image_record.id),
            "type": "bounding_box",
            "label": label,
            "confidence": conf,
            "geometry": norm_box,
            "pixel_geometry": pixel_geo,
            "geo_geometry": geo_geo,
            "artifact_key": None,
            "crop_artifact_key": None
        }
        processed_regions.append(evidence_entry)

    # 2. Render visual overlay and region crops
    try:
        try:
            pil_img = RemoteSensingPreprocessor.read_and_normalize_bands(image_bytes)
        except Exception:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        artifacts_map = await persist_evidence_artifacts(
            base_image=pil_img,
            regions=processed_regions,
            analysis_id=analysis_id
        )

        for reg in processed_regions:
            reg["artifact_key"] = artifacts_map.get("overlay_key")

    except Exception as e:
        logger.warning(f"Could not decode raster for visual evidence rendering: {e}")

    # 3. Persist evidence records to database
    if db:
        try:
            for entry in processed_regions:
                ev_record = EvidenceModel(
                    id=uuid.UUID(entry["id"]),
                    analysis_id=analysis_id,
                    image_id=image_record.id,
                    type=entry["type"],
                    label=entry["label"],
                    confidence=entry["confidence"],
                    geometry_json=entry["geometry"],
                    pixel_geometry_json=entry["pixel_geometry"],
                    geo_geometry_json=entry["geo_geometry"],
                    artifact_key=entry["artifact_key"],
                    crop_artifact_key=entry.get("crop_artifact_key")
                )
                db.add(ev_record)
            await db.flush()
            logger.info(f"Persisted {len(processed_regions)} evidence records for analysis '{analysis_id}'.")
        except Exception as e:
            logger.error(f"Failed to persist evidence to database: {e}", exc_info=True)

    return processed_regions
