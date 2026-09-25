"""
Analysis Service orchestrating remote-sensing AI queries,
model dispatch, lifecycle transitions, and database persistence.
"""

import datetime
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.exceptions import (
    AIError,
    InferenceError,
    ModelNotFoundError,
    ModelUnavailableError,
    UnsupportedModalityError,
)
from app.ai.runtime import get_model_runtime
from app.core.logging import logger
from app.database.models import AnalysisJobModel, ImageModel
from app.storage.object_store import get_object_store


class AnalysisService:
    """
    Central orchestration service for remote-sensing AI inference.
    Maps API requests and future Phase 3 Agent queries to the AI runtime.
    """

    @classmethod
    async def analyze(
        cls,
        task: str,
        image_id: uuid.UUID,
        query: Optional[str] = None,
        model_name: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Executes a specialist AI analysis on a registered satellite image.
        Persists lifecycle state progression in the database.
        """
        if not db:
            raise ValueError("Database session required for analysis execution.")

        start_time = time.time()

        # 1. Fetch image record
        stmt = select(ImageModel).where(ImageModel.id == image_id)
        res = await db.execute(stmt)
        image_record = res.scalar_one_or_none()
        if not image_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Satellite image '{image_id}' not found. Please upload an image first."
            )

        # 2. Resolve specialist model from registry
        runtime = get_model_runtime()
        try:
            if model_name:
                specialist_model = runtime.registry.get(model_name)
            else:
                specialist_model = runtime.registry.get_by_task(task)
        except ModelNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No AI model available for task '{task}': {str(e)}"
            )

        # 3. Create initial persistent job record (QUEUED)
        job_id = uuid.uuid4()
        job = AnalysisJobModel(
            id=job_id,
            image_id=image_id,
            task=task,
            query=query,
            model_name=specialist_model.name,
            model_version=specialist_model.version,
            status="queued",
            created_at=datetime.datetime.now(datetime.timezone.utc),
            started_at=datetime.datetime.now(datetime.timezone.utc),
        )
        db.add(job)
        await db.flush()

        # 4. Execute lifecycle stages with robust error tracking
        try:
            # Stage: VALIDATING
            job.status = "validating"
            await db.flush()

            image_metadata = {
                "modality": image_record.modality,
                "band_count": image_record.band_count,
                "dtype": image_record.dtype,
                "nodata": image_record.nodata,
                "width": image_record.width,
                "height": image_record.height,
            }

            specialist_model.validate_input(b"placeholder_for_precheck", image_metadata)

            # Stage: PREPROCESSING (Download raster from object storage)
            job.status = "preprocessing"
            await db.flush()

            store = get_object_store()
            image_bytes = await store.download_bytes(image_record.object_key)

            # Stage: RUNNING (Inference on target device)
            job.status = "running"
            await db.flush()

            result_contract = runtime.execute(
                model=specialist_model,
                image_bytes=image_bytes,
                metadata=image_metadata,
                query=query
            )

            # Stage: POSTPROCESSING & COMPLETED
            job.status = "postprocessing"
            await db.flush()

            # Process visual evidence if task produces regions (e.g. grounding)
            evidence_items = result_contract.get("evidence", [])
            raw_regions = result_contract.get("result", {}).get("regions", [])
            if raw_regions:
                from app.evidence.renderer import process_grounding_evidence
                evidence_items = await process_grounding_evidence(
                    raw_regions=raw_regions,
                    image_record=image_record,
                    image_bytes=image_bytes,
                    analysis_id=job_id,
                    db=db
                )

            duration_ms = int((time.time() - start_time) * 1000)
            job.status = "completed"
            job.result_json = result_contract["result"]
            job.confidence = result_contract.get("confidence", {}).get("score")
            job.confidence_method = result_contract.get("confidence", {}).get("method")
            job.processing_time_ms = duration_ms
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await db.flush()

            return {
                "analysis_id": job_id,
                "status": "completed",
                "task": task,
                "model": specialist_model.name,
                "model_version": specialist_model.version,
                "result": result_contract["result"],
                "confidence": job.confidence,
                "confidence_method": job.confidence_method,
                "evidence": evidence_items,
                "processing_time_ms": duration_ms,
                "is_adapted": getattr(specialist_model, "is_adapted", False) or result_contract.get("is_adapted", False),
                "adapter_metadata": result_contract.get("result", {}).get("adapter_metadata") or getattr(specialist_model, "adapter_metadata", None) or {"adapter_id": getattr(specialist_model, "adapter_id", specialist_model.name), "is_adapted": True},
                "fallback": result_contract.get("fallback"),
            }

        except UnsupportedModalityError as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "UNSUPPORTED_MODALITY",
                    "message": f"Unsupported modality: {str(e)}",
                    "details": {"image_id": str(image_id), "task": task}
                }
            )
        except ModelUnavailableError as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await db.flush()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "MODEL_UNAVAILABLE",
                    "message": f"The selected analysis model is currently unavailable: {str(e)}",
                    "details": {"model": specialist_model.name, "task": task}
                }
            )
        except InferenceError as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await db.flush()
            logger.error(f"Inference error on job '{job_id}': {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "MODEL_EXECUTION_FAILURE",
                    "message": f"Inference execution failed: {str(e)}",
                    "details": {"model": specialist_model.name, "task": task}
                }
            )
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            await db.flush()
            logger.error(f"Analysis job '{job_id}' failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "TOOL_EXECUTION_FAILURE",
                    "message": f"Analysis failed. No result was generated: {str(e)}",
                    "details": {"model": specialist_model.name, "task": task}
                }
            )

    @classmethod
    async def get_job(cls, job_id: uuid.UUID, db: AsyncSession) -> Optional[AnalysisJobModel]:
        stmt = select(AnalysisJobModel).where(AnalysisJobModel.id == job_id)
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis job '{job_id}' not found."
            )
        return record

    @classmethod
    async def list_jobs_for_image(
        cls, image_id: uuid.UUID, db: AsyncSession, limit: int = 20
    ) -> List[AnalysisJobModel]:
        stmt = (
            select(AnalysisJobModel)
            .where(AnalysisJobModel.image_id == image_id)
            .order_by(desc(AnalysisJobModel.created_at))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
