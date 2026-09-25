"""
Cross-Modal Pair & Joint Analysis Service for SatQuery AI.
Coordinates database persistence, image retrieval, modality validation,
non-destructive spatial alignment, specialist AI inference, visual evidence rendering,
and audit trace integration.
"""

import datetime
import io
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.cross_modal.alignment import CrossModalAlignmentEngine
from app.cross_modal.models import OpticalSARPairModel
from app.cross_modal.reasoning import CrossModalReasoningEngine
from app.cross_modal.schemas import (
    CrossModalAnalysisResponse,
    CrossModalEvidenceRegion,
    CrossModalValidationResult,
    OpticalSARPairCreate,
    OpticalSARPairResponse,
    PairImageSummary,
)
from app.cross_modal.validator import CrossModalValidator
from app.database.models import AnalysisJobModel, EvidenceModel, ImageModel
from app.database.session import async_session_factory
from app.storage.exceptions import StorageObjectNotFoundError
from app.storage.object_store import get_object_store


class CrossModalPairService:
    """
    Service coordinating Optical-SAR pair lifecycle and cross-modal intelligence.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def create_pair(
        self,
        create_req: OpticalSARPairCreate,
        db: Optional[AsyncSession] = None
    ) -> OpticalSARPairResponse:
        """
        Registers and validates a new OpticalSARPair record.
        Strictly enforces that one image is Optical/Multispectral and one image is SAR.
        """
        async with self._ensure_session(db) as session:
            # 1. Fetch images
            opt_img = await session.get(ImageModel, create_req.optical_image_id)
            if not opt_img:
                raise ValueError(f"Optical image with ID '{create_req.optical_image_id}' not found.")

            sar_img = await session.get(ImageModel, create_req.sar_image_id)
            if not sar_img:
                raise ValueError(f"SAR image with ID '{create_req.sar_image_id}' not found.")

            # 2. Execute validation
            val_result = CrossModalValidator.validate_pair(
                optical_image=opt_img,
                sar_image=sar_img,
            )

            # 3. Create persistent record
            pair_id = uuid.uuid4()
            pair_record = OpticalSARPairModel(
                id=pair_id,
                optical_image_id=opt_img.id,
                sar_image_id=sar_img.id,
                optical_modality=val_result.optical_modality,
                sar_modality=val_result.sar_modality,
                optical_sensor=opt_img.sensor,
                sar_sensor=sar_img.sensor,
                optical_acquisition_time=opt_img.acquisition_time,
                sar_acquisition_time=sar_img.acquisition_time,
                optical_crs=opt_img.crs,
                sar_crs=sar_img.crs,
                optical_resolution=opt_img.resolution_x,
                sar_resolution=sar_img.resolution_x,
                optical_bounds=opt_img.bounds,
                sar_bounds=sar_img.bounds,
                registration_status="UNALIGNED",
                spatial_compatibility="COMPATIBLE" if val_result.spatially_compatible else "INCOMPATIBLE",
                validation_status="VALID" if val_result.valid else "INVALID",
                overlap_ratio=val_result.overlap_ratio,
                alignment_method=None,
                alignment_metadata=None,
                validation_result_json=val_result.model_dump(),
            )

            session.add(pair_record)
            await session.commit()
            await session.refresh(pair_record)

            logger.info(f"Registered Optical-SAR pair {pair_id} [Valid={val_result.valid}].")
            return self._build_pair_response(pair_record, opt_img, sar_img, val_result)

    async def get_pair(
        self,
        pair_id: uuid.UUID,
        db: Optional[AsyncSession] = None
    ) -> Optional[OpticalSARPairResponse]:
        """Retrieves an OpticalSARPair record by ID."""
        async with self._ensure_session(db) as session:
            pair = await session.get(OpticalSARPairModel, pair_id)
            if not pair:
                return None
            opt_img = await session.get(ImageModel, pair.optical_image_id)
            sar_img = await session.get(ImageModel, pair.sar_image_id)
            val_result = CrossModalValidationResult(
                **pair.validation_result_json
            ) if pair.validation_result_json else CrossModalValidationResult(
                valid=pair.validation_status == "VALID",
                optical_valid=True,
                sar_valid=True,
                spatially_compatible=pair.spatial_compatibility == "COMPATIBLE",
                overlap_ratio=pair.overlap_ratio or 0.0,
                status_code="LOADED",
                message="Pair loaded from database.",
                optical_modality=pair.optical_modality,
                sar_modality=pair.sar_modality,
            )

            # Validate backing storage availability
            storage = get_object_store()
            opt_ok = await storage.exists(opt_img.object_key) if (opt_img and opt_img.object_key) else False
            sar_ok = await storage.exists(sar_img.object_key) if (sar_img and sar_img.object_key) else False
            if not (opt_ok and sar_ok):
                val_result.valid = False
                val_result.status_code = "INVALID_STORAGE"
                val_result.message = "One or both images in this optical-SAR pair are missing from object storage."

            return self._build_pair_response(pair, opt_img, sar_img, val_result)

    async def list_pairs(
        self,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> List[OpticalSARPairResponse]:
        """Lists registered OpticalSARPairs with pagination."""
        storage = get_object_store()
        async with self._ensure_session(db) as session:
            stmt = select(OpticalSARPairModel).order_by(OpticalSARPairModel.created_at.desc()).limit(limit).offset(offset)
            res = await session.execute(stmt)
            pairs = res.scalars().all()

            responses = []
            for pair in pairs:
                opt_img = await session.get(ImageModel, pair.optical_image_id)
                sar_img = await session.get(ImageModel, pair.sar_image_id)
                val_result = CrossModalValidationResult(
                    **pair.validation_result_json
                ) if pair.validation_result_json else CrossModalValidationResult(
                    valid=pair.validation_status == "VALID",
                    optical_valid=True,
                    sar_valid=True,
                    spatially_compatible=pair.spatial_compatibility == "COMPATIBLE",
                    overlap_ratio=pair.overlap_ratio or 0.0,
                    status_code="LOADED",
                    message="Pair loaded from database.",
                    optical_modality=pair.optical_modality,
                    sar_modality=pair.sar_modality,
                )
                opt_ok = await storage.exists(opt_img.object_key) if (opt_img and opt_img.object_key) else False
                sar_ok = await storage.exists(sar_img.object_key) if (sar_img and sar_img.object_key) else False
                if not (opt_ok and sar_ok):
                    val_result.valid = False
                    val_result.status_code = "INVALID_STORAGE"
                    val_result.message = "One or both images in this optical-SAR pair are missing from object storage."

                responses.append(self._build_pair_response(pair, opt_img, sar_img, val_result))
            return responses

    async def execute_cross_modal_analysis(
        self,
        pair_id: uuid.UUID,
        query: str = "Analyze these optical and SAR images together.",
        task: str = "cross_modal_analysis",
        db: Optional[AsyncSession] = None
    ) -> CrossModalAnalysisResponse:
        """
        Executes end-to-end Optical-SAR cross-modal pipeline:
        Alignment -> Specialist Model Inference -> Cross-Modal Reasoning -> Visual Evidence Overlay -> Persistence.
        """
        start_time = time.time()
        analysis_id = uuid.uuid4()
        storage = get_object_store()

        async with self._ensure_session(db) as session:
            # 1. Fetch pair and images
            pair = await session.get(OpticalSARPairModel, pair_id)
            if not pair:
                raise ValueError(f"OpticalSARPair with ID '{pair_id}' not found.")

            opt_img = await session.get(ImageModel, pair.optical_image_id)
            sar_img = await session.get(ImageModel, pair.sar_image_id)

            if not opt_img:
                raise StorageObjectNotFoundError(
                    message=f"Optical image '{pair.optical_image_id}' for pair '{pair_id}' not found in database.",
                    image_id=str(pair.optical_image_id),
                    storage_status="MISSING"
                )
            if not sar_img:
                raise StorageObjectNotFoundError(
                    message=f"SAR image '{pair.sar_image_id}' for pair '{pair_id}' not found in database.",
                    image_id=str(pair.sar_image_id),
                    storage_status="MISSING"
                )

            # Validate backing object existence in storage
            if not opt_img.object_key or not await storage.exists(opt_img.object_key):
                raise StorageObjectNotFoundError(
                    message=(
                        f"Optical image '{opt_img.original_filename or opt_img.id}' is registered in the catalog, "
                        f"but its original GeoTIFF is missing from object storage ({opt_img.object_key})."
                    ),
                    image_id=str(opt_img.id),
                    object_key=opt_img.object_key,
                    storage_status="MISSING"
                )

            if not sar_img.object_key or not await storage.exists(sar_img.object_key):
                raise StorageObjectNotFoundError(
                    message=(
                        f"SAR image '{sar_img.original_filename or sar_img.id}' is registered in the catalog, "
                        f"but its original GeoTIFF is missing from object storage ({sar_img.object_key})."
                    ),
                    image_id=str(sar_img.id),
                    object_key=sar_img.object_key,
                    storage_status="MISSING"
                )

            opt_bytes = await storage.download_bytes(opt_img.object_key)
            sar_bytes = await storage.download_bytes(sar_img.object_key)

            # 2. Co-registration / Non-destructive Alignment
            opt_array, aligned_sar, align_meta = CrossModalAlignmentEngine.align(
                optical_image=opt_img,
                sar_image=sar_img,
                optical_bytes=opt_bytes,
                sar_bytes=sar_bytes,
            )

            pair.registration_status = align_meta.get("status", "ALIGNED")
            pair.alignment_method = align_meta.get("method", "native_grid")
            pair.alignment_metadata = align_meta

            # 3. Model Inference via AI Runtime
            from app.ai.runtime import get_model_runtime
            runtime = get_model_runtime()
            model = runtime.get_model_for_task(task)
            if not model:
                # Fallback to general cross_modal_analysis model
                model = runtime.get_model_for_task("cross_modal_analysis")

            if not model:
                raise RuntimeError("No cross-modal specialist model registered in AI runtime.")

            model_output = model.predict(
                processed_input={"optical": opt_array, "sar": aligned_sar},
                query=query
            )

            # 4. Cross-Modal Reasoning
            sar_pol = CrossModalValidator.detect_sar_polarization(sar_img)
            reasoning_result = CrossModalReasoningEngine.reason(
                query=query,
                task=task,
                optical_meta={"sensor": opt_img.sensor, "modality": opt_img.modality},
                sar_meta={"sensor": sar_img.sensor, "modality": sar_img.modality, "polarization": sar_pol},
                model_prediction=model_output,
                optical_shape=(opt_img.height, opt_img.width),
                transform=opt_img.transform,
                crs=opt_img.crs,
            )

            regions = reasoning_result["regions"]

            # 5. Render & Upload Visual Evidence Artifact
            overlay_png_bytes = self._render_cross_modal_overlay(
                optical_array=opt_array,
                sar_array=aligned_sar,
                regions=regions
            )
            overlay_key = f"evidence/{analysis_id}/cross_modal_overlay.png"
            await storage.upload_bytes(
                key=overlay_key,
                data=overlay_png_bytes,
                content_type="image/png"
            )

            # 6. Persist Evidence Records
            evidence_entries: List[Dict[str, Any]] = []
            for r in regions:
                ev_id = uuid.uuid4()
                ev_record = EvidenceModel(
                    id=ev_id,
                    analysis_id=analysis_id,
                    image_id=opt_img.id,
                    type="CROSS_MODAL_REGION",
                    label=r.label,
                    confidence=r.confidence,
                    geometry_json=r.bbox,
                    pixel_geometry_json=r.pixel_geometry,
                    geo_geometry_json=r.geo_geometry,
                    artifact_key=overlay_key,
                    crop_artifact_key=None,
                )
                session.add(ev_record)
                evidence_entries.append({
                    "id": str(ev_id),
                    "type": "CROSS_MODAL_REGION",
                    "label": r.label,
                    "confidence": r.confidence,
                    "geometry": r.bbox,
                    "pixel_geometry": r.pixel_geometry,
                    "geo_geometry": r.geo_geometry,
                    "artifact_key": overlay_key,
                    "supported_by": r.supported_by,
                })

            duration_ms = int((time.time() - start_time) * 1000)

            # 7. Persist AnalysisJobModel
            job = AnalysisJobModel(
                id=analysis_id,
                image_id=opt_img.id,
                cross_modal_pair_id=pair_id,
                task=task,
                query=query,
                model_name=getattr(model, "name", "cross-modal-specialist"),
                model_version=getattr(model, "version", "1.0.0"),
                status="completed",
                result_json={
                    "answer": reasoning_result["answer"],
                    "observations": reasoning_result["observations"],
                    "optical_summary": reasoning_result["optical_summary"].model_dump(),
                    "sar_summary": reasoning_result["sar_summary"].model_dump(),
                    "disagreement": reasoning_result["disagreement"].model_dump(),
                    "regions_count": len(regions),
                },
                confidence=reasoning_result["confidence_score"],
                confidence_method=reasoning_result["confidence_method"],
                processing_time_ms=duration_ms,
            )
            session.add(job)
            await session.commit()

            return CrossModalAnalysisResponse(
                analysis_id=analysis_id,
                task=task.upper(),
                pair_id=pair_id,
                query=query,
                answer=reasoning_result["answer"],
                optical_summary=reasoning_result["optical_summary"],
                sar_summary=reasoning_result["sar_summary"],
                joint_observations=reasoning_result["observations"],
                disagreement=reasoning_result["disagreement"],
                regions=regions,
                confidence={
                    "score": reasoning_result["confidence_score"],
                    "method": reasoning_result["confidence_method"]
                },
                evidence=evidence_entries,
                processing={
                    "alignment_performed": align_meta.get("status") != "NOT_REQUIRED",
                    "alignment_method": align_meta.get("method"),
                    "model": getattr(model, "name", "cross-modal-specialist"),
                    "duration_ms": duration_ms,
                }
            )

    def _render_cross_modal_overlay(
        self,
        optical_array: np.ndarray,
        sar_array: np.ndarray,
        regions: List[CrossModalEvidenceRegion]
    ) -> bytes:
        """Renders bounding regions and joint highlights onto an RGB visual composite."""
        h, w = optical_array.shape[:2]
        # Base image: standard 3-channel RGB representation
        if optical_array.ndim == 3 and optical_array.shape[2] >= 3:
            base_rgb = optical_array[:, :, :3].copy()
        elif optical_array.ndim == 3:
            base_rgb = np.repeat(optical_array[:, :, :1], 3, axis=-1)
        else:
            base_rgb = np.repeat(np.expand_dims(optical_array, -1), 3, axis=-1)

        pil_img = Image.fromarray(base_rgb.astype(np.uint8)).convert("RGBA")
        overlay = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        for r in regions:
            px = r.pixel_geometry
            x1, y1, x2, y2 = px["x1"], px["y1"], px["x2"], px["y2"]
            # Color code: cyan for both, yellow for optical, magenta for sar
            if r.supported_by == "optical":
                box_color = (234, 179, 8, 240)
                fill_color = (234, 179, 8, 40)
            elif r.supported_by == "sar":
                box_color = (236, 72, 153, 240)
                fill_color = (236, 72, 153, 40)
            else:
                box_color = (6, 182, 212, 240)
                fill_color = (6, 182, 212, 45)

            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=3, fill=fill_color)

        combined = Image.alpha_composite(pil_img, overlay).convert("RGB")
        buf = io.BytesIO()
        combined.save(buf, format="PNG")
        return buf.getvalue()

    def _build_pair_response(
        self,
        pair: OpticalSARPairModel,
        opt_img: ImageModel,
        sar_img: ImageModel,
        val_result: CrossModalValidationResult,
    ) -> OpticalSARPairResponse:
        """Constructs an OpticalSARPairResponse schema."""
        sar_pol = CrossModalValidator.detect_sar_polarization(sar_img)
        opt_summary = PairImageSummary(
            id=opt_img.id,
            original_filename=opt_img.original_filename,
            modality=opt_img.modality,
            sensor=opt_img.sensor,
            crs=opt_img.crs,
            resolution=opt_img.resolution_x,
            bounds=opt_img.bounds,
            acquisition_time=opt_img.acquisition_time,
            band_count=opt_img.band_count,
            dtype=opt_img.dtype,
            polarization=None,
        )
        sar_summary = PairImageSummary(
            id=sar_img.id,
            original_filename=sar_img.original_filename,
            modality=sar_img.modality,
            sensor=sar_img.sensor,
            crs=sar_img.crs,
            resolution=sar_img.resolution_x,
            bounds=sar_img.bounds,
            acquisition_time=sar_img.acquisition_time,
            band_count=sar_img.band_count,
            dtype=sar_img.dtype,
            polarization=sar_pol,
        )

        return OpticalSARPairResponse(
            id=pair.id,
            optical_image=opt_summary,
            sar_image=sar_summary,
            optical_modality=pair.optical_modality,
            sar_modality=pair.sar_modality,
            optical_sensor=pair.optical_sensor,
            sar_sensor=pair.sar_sensor,
            spatial_compatibility=pair.spatial_compatibility,
            registration_status=pair.registration_status,
            validation_status=pair.validation_status,
            overlap_ratio=pair.overlap_ratio,
            alignment_method=pair.alignment_method,
            alignment_metadata=pair.alignment_metadata,
            validation=val_result,
            created_at=pair.created_at,
            updated_at=pair.updated_at,
        )

    def _ensure_session(self, db: Optional[AsyncSession]):
        if db is not None:
            class _NoOpContext:
                async def __aenter__(self):
                    return db
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return _NoOpContext()
        return async_session_factory()


_cross_modal_service: Optional[CrossModalPairService] = None


def get_cross_modal_service() -> CrossModalPairService:
    global _cross_modal_service
    if _cross_modal_service is None:
        _cross_modal_service = CrossModalPairService()
    return _cross_modal_service
