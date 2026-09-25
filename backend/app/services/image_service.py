import hashlib
import time
import uuid
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.security import generate_storage_keys, sanitize_filename, validate_file_extension
from app.database.models import ImageModel, ImageMetadataModel
from app.geospatial.metadata import MetadataExtractor
from app.geospatial.preview import PreviewGenerator
from app.geospatial.validator import GeospatialValidator
from app.schemas.image import (
    BoundingBoxSchema,
    GeospatialMetadataSchema,
    ImageInspectResponse,
    ImageUploadResponse,
    ImageValidationResponse,
    RasterMetadataSchema,
    ResolutionSchema,
    ValidationResultSchema,
)
from app.storage.object_store import get_object_store


class ImageService:
    """Service orchestrating ingestion, metadata extraction, validation, and storage."""

    @classmethod
    async def upload_and_process(
        cls,
        file_bytes: bytes,
        original_filename: str,
        db: AsyncSession
    ) -> ImageUploadResponse:
        start_time = time.time()
        clean_name = sanitize_filename(original_filename)

        # 1. Content & Format Validation
        val_res = GeospatialValidator.validate_file_content(file_bytes, clean_name)
        if not val_res.valid:
            error_msg = "; ".join(val_res.errors) if val_res.errors else "File failed raster validation."
            logger.warning(
                f"Validation failed for upload: {clean_name}",
                extra={"operation": "upload_validate", "status": "failed", "errors": val_res.errors}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation failed: {error_msg}"
            )

        # 2. Assign internal UUID and compute checksum
        image_id = uuid.uuid4()
        checksum = hashlib.sha256(file_bytes).hexdigest()
        file_size = len(file_bytes)

        # 3. Generate secure isolated storage keys
        _, ext = validate_file_extension(clean_name)
        orig_key, preview_key = generate_storage_keys(image_id, ext)

        # 4. Extract raster and geospatial metadata
        meta = MetadataExtractor.extract(file_bytes, clean_name)

        # Merge validator warnings if any
        all_warnings = list(set(val_res.warnings + meta.warnings))
        val_status = "warning" if all_warnings else "valid"

        # 5. Generate browser-friendly preview
        preview_out = PreviewGenerator.generate(file_bytes, nodata=meta.nodata)

        # 6. Persist to Object Storage
        store = get_object_store()
        mime = "image/tiff" if meta.format_name in ("GeoTIFF", "TIFF") else f"image/{meta.format_name.lower()}"
        await store.upload_bytes(orig_key, file_bytes, content_type=mime)
        await store.upload_bytes(preview_key, preview_out.image_bytes, content_type=preview_out.mime_type)

        # 7. Persist to Database
        image_record = ImageModel(
            id=image_id,
            original_filename=clean_name,
            object_key=orig_key,
            preview_key=preview_key,
            mime_type=mime,
            file_format=meta.format_name,
            file_size=file_size,
            checksum=checksum,
            width=meta.width,
            height=meta.height,
            band_count=meta.bands,
            dtype=meta.dtype,
            nodata=meta.nodata,
            crs=meta.crs_str,
            epsg_code=meta.epsg_code,
            resolution_x=meta.resolution_x,
            resolution_y=meta.resolution_y,
            bounds=meta.bounds,
            transform=meta.transform,
            modality=meta.modality,
            is_geospatial=meta.is_geospatial,
            validation_status=val_status,
        )
        db.add(image_record)

        # Extensible metadata entry
        meta_entry = ImageMetadataModel(
            image_id=image_id,
            metadata_json={
                "preview": {
                    "width": preview_out.width,
                    "height": preview_out.height,
                    "selected_bands": preview_out.selected_bands,
                    "normalization": preview_out.normalization_method
                },
                "warnings": all_warnings
            }
        )
        db.add(meta_entry)
        await db.flush()

        duration = int((time.time() - start_time) * 1000)
        logger.info(
            f"Successfully ingested image {image_id}",
            extra={
                "image_id": str(image_id),
                "operation": "ingest",
                "status": "success",
                "duration_ms": duration,
                "file_format": meta.format_name,
                "size_bytes": file_size
            }
        )

        return ImageUploadResponse(
            id=image_id,
            filename=clean_name,
            status=val_status,
            message="Image uploaded, validated, and processed successfully"
        )

    @classmethod
    async def get_inspect_response(
        cls,
        image_id: uuid.UUID,
        db: AsyncSession,
        cached_record: Optional[ImageModel] = None
    ) -> ImageInspectResponse:
        record = cached_record
        if not record:
            stmt = select(ImageModel).where(ImageModel.id == image_id)
            result = await db.execute(stmt)
            record = result.scalar_one_or_none()
            if not record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image with ID {image_id} not found."
                )

        # Retrieve warnings from extensible metadata if present (ImageMetadataModel is optional)
        warnings: list[str] = []
        try:
            stmt_meta = select(ImageMetadataModel).where(ImageMetadataModel.image_id == image_id)
            meta_res = await db.execute(stmt_meta)
            meta_record = meta_res.scalar_one_or_none()
            if meta_record and isinstance(meta_record.metadata_json, dict):
                raw_warnings = meta_record.metadata_json.get("warnings", [])
                if isinstance(raw_warnings, list):
                    warnings = [str(w) for w in raw_warnings]
        except Exception as e:
            logger.debug(f"Notice retrieving metadata warnings for image {image_id}: {e}")
            warnings = []

        bounds_schema = None
        if record.bounds and isinstance(record.bounds, dict):
            bounds_schema = BoundingBoxSchema(
                left=float(record.bounds.get("left", 0.0)),
                bottom=float(record.bounds.get("bottom", 0.0)),
                right=float(record.bounds.get("right", 0.0)),
                top=float(record.bounds.get("top", 0.0)),
            )

        res_schema = None
        if record.resolution_x is not None and record.resolution_y is not None:
            res_schema = ResolutionSchema(
                x=float(record.resolution_x),
                y=float(record.resolution_y)
            )

        transform_list = None
        if record.transform:
            if isinstance(record.transform, (list, tuple)):
                transform_list = [float(x) for x in record.transform]
            elif isinstance(record.transform, dict):
                transform_list = [float(v) for v in record.transform.values()]

        return ImageInspectResponse(
            id=record.id,
            filename=record.original_filename or "unnamed_raster",
            format=record.file_format or "unknown",
            size_bytes=int(record.file_size or 0),
            modality=record.modality or "unknown",
            raster=RasterMetadataSchema(
                width=int(record.width or 0),
                height=int(record.height or 0),
                bands=int(record.band_count or 1),
                dtype=str(record.dtype or "uint8"),
                nodata=float(record.nodata) if record.nodata is not None else None
            ),
            geospatial=GeospatialMetadataSchema(
                is_geospatial=bool(record.is_geospatial),
                crs=record.crs,
                epsg=record.epsg_code,
                bounds=bounds_schema,
                resolution=res_schema,
                transform=transform_list
            ),
            validation=ValidationResultSchema(
                valid=(record.validation_status != "error"),
                warnings=warnings,
                errors=[]
            )
        )

    @classmethod
    async def validate_image(cls, image_id: uuid.UUID, db: AsyncSession) -> ImageValidationResponse:
        inspect = await cls.get_inspect_response(image_id, db)
        return ImageValidationResponse(
            valid=inspect.validation.valid,
            warnings=inspect.validation.warnings,
            errors=inspect.validation.errors,
            metadata=inspect
        )

    @classmethod
    async def get_preview_bytes(cls, image_id: uuid.UUID, db: AsyncSession) -> Tuple[bytes, str]:
        stmt = select(ImageModel).where(ImageModel.id == image_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record or not record.preview_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PREVIEW_NOT_FOUND: No preview key registered for this image."
            )

        store = get_object_store()
        try:
            preview_bytes = await store.download_bytes(record.preview_key)
            return preview_bytes, "image/png"
        except Exception as e:
            logger.warning(f"Error downloading preview key {record.preview_key}: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="PREVIEW_NOT_FOUND: Preview raster object not found in storage."
            )

    @classmethod
    async def delete_image(cls, image_id: uuid.UUID, db: AsyncSession) -> bool:
        stmt = select(ImageModel).where(ImageModel.id == image_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found."
            )

        store = get_object_store()
        # Delete object and preview from storage
        if record.object_key:
            await store.delete_object(record.object_key)
        if record.preview_key:
            await store.delete_object(record.preview_key)

        # Delete database record
        await db.delete(record)
        await db.flush()

        logger.info(f"Deleted image {image_id} from database and storage.")
        return True

    @classmethod
    async def list_images(cls, db: AsyncSession, limit: int = 50) -> list[ImageInspectResponse]:
        try:
            stmt = select(ImageModel).order_by(ImageModel.created_at.desc()).limit(limit)
            res = await db.execute(stmt)
            records = res.scalars().all()
        except Exception as e:
            logger.error(f"Error querying images from database: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "DATABASE_SCHEMA_MISMATCH",
                    "message": f"Database schema mismatch while querying images table: {str(e)}",
                    "details": {"error": str(e)}
                }
            )

        responses: list[ImageInspectResponse] = []
        for record in records:
            try:
                responses.append(await cls.get_inspect_response(record.id, db, cached_record=record))
            except Exception as e:
                logger.warning(f"Error building inspect response for image {record.id}: {e}")
        return responses
