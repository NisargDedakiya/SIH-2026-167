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
    async def get_inspect_response(cls, image_id: uuid.UUID, db: AsyncSession) -> ImageInspectResponse:
        stmt = select(ImageModel).where(ImageModel.id == image_id)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image with ID {image_id} not found."
            )

        # Retrieve warnings from extensible metadata if present
        stmt_meta = select(ImageMetadataModel).where(ImageMetadataModel.image_id == image_id)
        meta_res = await db.execute(stmt_meta)
        meta_record = meta_res.scalar_one_or_none()
        warnings = meta_record.metadata_json.get("warnings", []) if meta_record else []

        bounds_schema = None
        if record.bounds and isinstance(record.bounds, dict):
            bounds_schema = BoundingBoxSchema(
                left=record.bounds.get("left", 0.0),
                bottom=record.bounds.get("bottom", 0.0),
                right=record.bounds.get("right", 0.0),
                top=record.bounds.get("top", 0.0),
            )

        res_schema = None
        if record.resolution_x is not None and record.resolution_y is not None:
            res_schema = ResolutionSchema(
                x=record.resolution_x,
                y=record.resolution_y
            )

        return ImageInspectResponse(
            id=record.id,
            filename=record.original_filename,
            format=record.file_format,
            size_bytes=record.file_size,
            modality=record.modality,
            raster=RasterMetadataSchema(
                width=record.width,
                height=record.height,
                bands=record.band_count,
                dtype=record.dtype,
                nodata=record.nodata
            ),
            geospatial=GeospatialMetadataSchema(
                is_geospatial=record.is_geospatial,
                crs=record.crs,
                epsg=record.epsg_code,
                bounds=bounds_schema,
                resolution=res_schema,
                transform=record.transform
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
                detail="Preview not found for this image."
            )

        store = get_object_store()
        try:
            preview_bytes = await store.download_bytes(record.preview_key)
            return preview_bytes, "image/png"
        except Exception as e:
            logger.error(f"Error downloading preview key {record.preview_key}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve preview image from storage."
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
        stmt = select(ImageModel).order_by(ImageModel.created_at.desc()).limit(limit)
        res = await db.execute(stmt)
        records = res.scalars().all()
        return [await cls.get_inspect_response(record.id, db) for record in records]
