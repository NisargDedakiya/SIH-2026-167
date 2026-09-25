"""
Temporal Pair & Change Analysis Service.
Coordinates database persistence, image retrieval, pair validation, alignment execution,
specialist inference, and visual evidence rendering.
"""

import datetime
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.runtime import get_model_runtime
from app.core.logging import logger
from app.database.models import AnalysisJobModel, BiTemporalPairModel, EvidenceModel, ImageModel
from app.database.session import async_session_factory
from app.evidence.geometry import pixel_bbox_to_geo_bounds
from app.storage.exceptions import StorageObjectNotFoundError
from app.storage.object_store import get_object_store
from app.temporal.alignment import AlignmentEngine
from app.temporal.change_map import ChangeMap
from app.temporal.change_vqa import ChangeVQAEngine
from app.temporal.description import ChangeDescriptionEngine
from app.temporal.regions import ChangeRegionExtractor
from app.temporal.schemas import (
    BiTemporalPairCreate,
    BiTemporalPairResponse,
    ChangeAnalysisResponse,
    ChangeAnalysisSummary,
    ChangeRegion,
    PairImageSummary,
    PairValidationResult,
    ProcessingDetails,
)
from app.temporal.validator import BiTemporalValidator


class TemporalPairService:
    """
    Service coordinating bi-temporal pair lifecycle and change detection analysis.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    async def create_pair(
        self,
        create_req: Optional[BiTemporalPairCreate] = None,
        request: Optional[BiTemporalPairCreate] = None,
        db: Optional[AsyncSession] = None
    ) -> BiTemporalPairResponse:
        """
        Registers and validates a new BiTemporalPair record.
        """
        req = create_req or request
        if not req:
            raise ValueError("BiTemporalPairCreate payload is required.")
        create_req = req
        async with self._ensure_session(db) as session:
            # 1. Fetch T1 and T2 images
            img_t1 = await session.get(ImageModel, create_req.image_t1_id)
            if not img_t1:
                raise ValueError(f"Image T1 with ID '{create_req.image_t1_id}' not found.")

            img_t2 = await session.get(ImageModel, create_req.image_t2_id)
            if not img_t2:
                raise ValueError(f"Image T2 with ID '{create_req.image_t2_id}' not found.")

            # 2. Execute validation
            val_result = BiTemporalValidator.validate_pair(
                image_t1=img_t1,
                image_t2=img_t2,
                override_t1_time=create_req.acquisition_time_t1,
                override_t2_time=create_req.acquisition_time_t2
            )

            # 3. Create persistent model
            pair_id = uuid.uuid4()
            t1_time = create_req.acquisition_time_t1 or img_t1.acquisition_time
            t2_time = create_req.acquisition_time_t2 or img_t2.acquisition_time

            pair_record = BiTemporalPairModel(
                id=pair_id,
                image_t1_id=img_t1.id,
                image_t2_id=img_t2.id,
                acquisition_time_t1=t1_time,
                acquisition_time_t2=t2_time,
                spatially_compatible=val_result.spatially_compatible,
                temporally_valid=val_result.temporal_valid,
                overlap_ratio=val_result.overlap_ratio,
                crs_t1=img_t1.crs,
                crs_t2=img_t2.crs,
                resolution_t1=img_t1.resolution_x,
                resolution_t2=img_t2.resolution_x,
                bounds_t1=img_t1.bounds,
                bounds_t2=img_t2.bounds,
                alignment_status="NOT_REQUIRED" if not val_result.warnings else "PENDING",
                registration_method=None,
                registration_metadata=None,
                validation_result_json=val_result.model_dump(),
            )
            session.add(pair_record)
            await session.commit()
            await session.refresh(pair_record)

            logger.info(f"Registered BiTemporalPair '{pair_id}' (valid={val_result.valid}, overlap={val_result.overlap_ratio}).")
            return self._build_pair_response(pair_record, img_t1, img_t2, val_result)

    async def get_pair(
        self,
        pair_id: uuid.UUID,
        db: Optional[AsyncSession] = None
    ) -> Optional[BiTemporalPairResponse]:
        """
        Retrieves a BiTemporalPair by UUID.
        """
        async with self._ensure_session(db) as session:
            pair = await session.get(BiTemporalPairModel, pair_id)
            if not pair:
                return None

            img_t1 = await session.get(ImageModel, pair.image_t1_id)
            img_t2 = await session.get(ImageModel, pair.image_t2_id)
            val_result = PairValidationResult(**pair.validation_result_json) if pair.validation_result_json else PairValidationResult(
                valid=pair.spatially_compatible and pair.temporally_valid,
                temporal_valid=pair.temporally_valid,
                spatially_compatible=pair.spatially_compatible,
                overlap_ratio=pair.overlap_ratio or 0.0,
                status_code="LOADED",
                message="Pair retrieved from database."
            )

            # Validate backing storage availability
            storage = get_object_store()
            t1_ok = await storage.exists(img_t1.object_key) if (img_t1 and img_t1.object_key) else False
            t2_ok = await storage.exists(img_t2.object_key) if (img_t2 and img_t2.object_key) else False
            if not (t1_ok and t2_ok):
                val_result.valid = False
                val_result.status_code = "INVALID_STORAGE"
                val_result.message = "One or both images in this temporal pair are missing from object storage."

            return self._build_pair_response(pair, img_t1, img_t2, val_result)

    async def list_pairs(
        self,
        limit: int = 50,
        offset: int = 0,
        db: Optional[AsyncSession] = None
    ) -> List[BiTemporalPairResponse]:
        """
        Lists registered bi-temporal pairs ordered chronologically descending.
        """
        storage = get_object_store()
        async with self._ensure_session(db) as session:
            stmt = (
                select(BiTemporalPairModel)
                .order_by(BiTemporalPairModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            res = await session.execute(stmt)
            pairs = res.scalars().all()

            results: List[BiTemporalPairResponse] = []
            for pair in pairs:
                img_t1 = await session.get(ImageModel, pair.image_t1_id)
                img_t2 = await session.get(ImageModel, pair.image_t2_id)
                val_result = PairValidationResult(**pair.validation_result_json) if pair.validation_result_json else PairValidationResult(
                    valid=pair.spatially_compatible and pair.temporally_valid,
                    temporal_valid=pair.temporally_valid,
                    spatially_compatible=pair.spatially_compatible,
                    overlap_ratio=pair.overlap_ratio or 0.0,
                    status_code="LOADED",
                    message="Pair retrieved from database."
                )
                t1_ok = await storage.exists(img_t1.object_key) if (img_t1 and img_t1.object_key) else False
                t2_ok = await storage.exists(img_t2.object_key) if (img_t2 and img_t2.object_key) else False
                if not (t1_ok and t2_ok):
                    val_result.valid = False
                    val_result.status_code = "INVALID_STORAGE"
                    val_result.message = "One or both images in this temporal pair are missing from object storage."

                results.append(self._build_pair_response(pair, img_t1, img_t2, val_result))

            return results


    async def execute_change_analysis(
        self,
        pair_id: uuid.UUID,
        query: str = "What changed between these two images?",
        threshold: float = 0.35,
        min_region_size: int = 25,
        db: Optional[AsyncSession] = None
    ) -> ChangeAnalysisResponse:
        """
        Executes end-to-end bi-temporal change detection or change VQA workflow.
        """
        start_time = time.time()
        analysis_id = uuid.uuid4()
        storage = get_object_store()

        async with self._ensure_session(db) as session:
            # 1. Fetch pair and images
            pair = await session.get(BiTemporalPairModel, pair_id)
            if not pair:
                raise ValueError(f"BiTemporalPair with ID '{pair_id}' not found.")

            img_t1 = await session.get(ImageModel, pair.image_t1_id)
            img_t2 = await session.get(ImageModel, pair.image_t2_id)

            if not img_t1:
                raise StorageObjectNotFoundError(
                    message=f"T1 image '{pair.image_t1_id}' for pair '{pair_id}' not found in database.",
                    image_id=str(pair.image_t1_id),
                    storage_status="MISSING"
                )
            if not img_t2:
                raise StorageObjectNotFoundError(
                    message=f"T2 image '{pair.image_t2_id}' for pair '{pair_id}' not found in database.",
                    image_id=str(pair.image_t2_id),
                    storage_status="MISSING"
                )

            # Validate backing object existence in storage
            if not img_t1.object_key or not await storage.exists(img_t1.object_key):
                raise StorageObjectNotFoundError(
                    message=(
                        f"Temporal T1 image '{img_t1.original_filename or img_t1.id}' is registered in the catalog, "
                        f"but its original GeoTIFF is missing from object storage ({img_t1.object_key})."
                    ),
                    image_id=str(img_t1.id),
                    object_key=img_t1.object_key,
                    storage_status="MISSING"
                )

            if not img_t2.object_key or not await storage.exists(img_t2.object_key):
                raise StorageObjectNotFoundError(
                    message=(
                        f"Temporal T2 image '{img_t2.original_filename or img_t2.id}' is registered in the catalog, "
                        f"but its original GeoTIFF is missing from object storage ({img_t2.object_key})."
                    ),
                    image_id=str(img_t2.id),
                    object_key=img_t2.object_key,
                    storage_status="MISSING"
                )

            t1_bytes = await storage.download_bytes(img_t1.object_key)
            t2_bytes = await storage.download_bytes(img_t2.object_key)

            # 2. Co-registration / Alignment
            t1_rgb, aligned_t2_rgb, align_meta = AlignmentEngine.align_pair(
                image_t1=img_t1,
                image_t2=img_t2,
                t1_bytes=t1_bytes,
                t2_bytes=t2_bytes
            )

            pair.alignment_status = align_meta.get("status", "NOT_REQUIRED")
            pair.registration_method = align_meta.get("method", "none")
            pair.registration_metadata = align_meta

            # 3. Model Inference via Runtime
            runtime = get_model_runtime()
            model = runtime.get_model_for_task("change_analysis")
            if not model:
                # Try fallback task alias
                model = runtime.get_model_for_task("change_detection")

            if not model:
                raise RuntimeError("No change detection model registered in AI runtime.")

            model_output = model.predict(
                processed_input={"t1": t1_rgb, "t2": aligned_t2_rgb},
                query=query
            )

            # 4. Generate Change Map & Extract Regions
            change_mask = model_output.get("change_mask")
            change_scores = model_output.get("change_scores")

            change_map = ChangeMap(
                change_mask=change_mask,
                change_scores=change_scores,
                threshold=threshold
            )

            regions = ChangeRegionExtractor.extract_regions(
                change_map=change_map,
                transform=img_t1.transform,
                crs=img_t1.crs,
                min_region_size=min_region_size,
                max_regions=15
            )

            # 5. Answer / Description Synthesis
            q_lower = query.lower()
            is_vqa_query = (
                "?" in query
                or any(q_lower.startswith(w) for w in ["did", "is", "has", "are", "where", "what type", "how many"])
                or any(w in q_lower for w in ["increase", "decrease", "more", "less", "new"])
            ) and not ("what changed" in q_lower and len(q_lower.split()) <= 6)

            if is_vqa_query:
                vqa_res = ChangeVQAEngine.answer_question(
                    query=query,
                    change_map=change_map,
                    regions=regions
                )
                answer = vqa_res["answer"]
                conf_score = vqa_res["confidence_score"]
                conf_method = vqa_res["confidence_method"]
            else:
                answer = ChangeDescriptionEngine.generate_description(
                    change_map=change_map,
                    regions=regions,
                    query=query
                )
                conf_score = max(0.85, change_map.mean_change_confidence)
                conf_method = "bitemporal_spatial_change_coverage"

            # 6. Render & Upload Visual Evidence Artifacts
            overlay_png = change_map.to_png_bytes(base_rgb=aligned_t2_rgb)
            overlay_key = f"evidence/{analysis_id}/change_overlay.png"
            await storage.upload_bytes(
                key=overlay_key,
                data=overlay_png,
                content_type="image/png"
            )

            # 7. Persist Evidence & Analysis Job Records
            evidence_entries: List[Dict[str, Any]] = []
            for r in regions:
                ev_id = uuid.uuid4()
                ev_record = EvidenceModel(
                    id=ev_id,
                    analysis_id=analysis_id,
                    image_id=img_t2.id,
                    type="CHANGE_REGION",
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
                    "type": "CHANGE_REGION",
                    "label": r.label,
                    "confidence": r.confidence,
                    "geometry": r.bbox,
                    "pixel_geometry": r.pixel_geometry,
                    "geo_geometry": r.geo_geometry,
                    "artifact_key": overlay_key
                })

            duration_ms = int((time.time() - start_time) * 1000)

            job = AnalysisJobModel(
                id=analysis_id,
                image_id=img_t2.id,
                pair_id=pair_id,
                task="change_analysis",
                query=query,
                model_name=model.name,
                model_version=model.version,
                status="completed",
                result_json={
                    "answer": answer,
                    "change_score": change_map.change_percentage / 100.0,
                    "change_percentage": change_map.change_percentage,
                    "regions_count": len(regions),
                    "regions": [r.model_dump() for r in regions],
                },
                confidence=conf_score,
                confidence_method=conf_method,
                processing_time_ms=duration_ms,
            )
            session.add(job)
            await session.commit()

            return ChangeAnalysisResponse(
                analysis_id=analysis_id,
                task="CHANGE_ANALYSIS",
                pair_id=pair_id,
                answer=answer,
                change=ChangeAnalysisSummary(
                    detected=change_map.has_change,
                    change_score=round(change_map.change_percentage / 100.0, 4),
                    change_percentage=change_map.change_percentage,
                    regions_count=len(regions),
                    threshold_used=threshold
                ),
                regions=regions,
                confidence={"score": conf_score, "method": conf_method},
                evidence=evidence_entries,
                processing=ProcessingDetails(
                    alignment_performed=align_meta.get("status") != "NOT_REQUIRED",
                    registration_method=align_meta.get("method"),
                    model=model.name,
                    model_version=model.version,
                    processing_time_ms=duration_ms
                ),
                artifact_key=overlay_key,
                change_map_key=overlay_key,
                trace_id=None
            )

    def _build_pair_response(
        self,
        pair: BiTemporalPairModel,
        t1: ImageModel,
        t2: ImageModel,
        validation: PairValidationResult
    ) -> BiTemporalPairResponse:
        return BiTemporalPairResponse(
            pair_id=pair.id,
            image_t1=PairImageSummary(
                id=t1.id,
                filename=t1.original_filename,
                acquisition_time=pair.acquisition_time_t1 or t1.acquisition_time,
                crs=t1.crs,
                width=t1.width,
                height=t1.height,
                resolution_x=t1.resolution_x,
                resolution_y=t1.resolution_y,
            ),
            image_t2=PairImageSummary(
                id=t2.id,
                filename=t2.original_filename,
                acquisition_time=pair.acquisition_time_t2 or t2.acquisition_time,
                crs=t2.crs,
                width=t2.width,
                height=t2.height,
                resolution_x=t2.resolution_x,
                resolution_y=t2.resolution_y,
            ),
            acquisition_time_t1=pair.acquisition_time_t1,
            acquisition_time_t2=pair.acquisition_time_t2,
            spatially_compatible=pair.spatially_compatible,
            temporally_valid=pair.temporally_valid,
            overlap_ratio=pair.overlap_ratio,
            alignment_status=pair.alignment_status,
            registration_method=pair.registration_method,
            registration_metadata=pair.registration_metadata,
            validation=validation,
            created_at=pair.created_at,
        )

    def _ensure_session(self, db: Optional[AsyncSession]):
        if db is not None:
            class SessionContext:
                def __init__(self, s): self.s = s
                async def __aenter__(self): return self.s
                async def __aexit__(self, *args): pass
            return SessionContext(db)
        return get_db_session()


_temporal_service: Optional[TemporalPairService] = None

def get_temporal_service() -> TemporalPairService:
    global _temporal_service
    if _temporal_service is None:
        _temporal_service = TemporalPairService()
    return _temporal_service
