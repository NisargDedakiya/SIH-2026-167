import uuid
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.image import (
    ImageInspectResponse,
    ImageUploadResponse,
    ImageValidationResponse,
)
from app.services.image_service import ImageService

router = APIRouter()


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload & Ingest Remote Sensing Image",
    description="Accepts GeoTIFF, TIFF, PNG, or JPEG raster files. Validates format, extracts metadata, generates browser preview, and securely stores the image."
)
async def upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename missing from upload payload."
        )

    file_bytes = await file.read()
    return await ImageService.upload_and_process(
        file_bytes=file_bytes,
        original_filename=file.filename,
        db=db
    )


@router.get(
    "",
    response_model=list[ImageInspectResponse],
    summary="List Uploaded Images",
    description="Retrieves a list of recent uploaded remote sensing images."
)
async def list_images(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    return await ImageService.list_images(db=db, limit=limit)


@router.get(
    "/{image_id}",
    response_model=ImageInspectResponse,
    summary="Inspect Remote Sensing Image Metadata",
    description="Retrieves complete raster technical specs, coordinate reference system (CRS), bounds, and validation report for an image."
)
async def get_image_metadata(
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await ImageService.get_inspect_response(image_id, db)


@router.post(
    "/{image_id}/validate",
    response_model=ImageValidationResponse,
    summary="Revalidate Image Status",
    description="Inspects and validates the given image against geospatial standards and returns warnings or errors."
)
async def validate_image(
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await ImageService.validate_image(image_id, db)


@router.get(
    "/{image_id}/storage-status",
    summary="Check Object Storage Existence",
    description="Verifies whether the original raster and preview files exist in backing storage."
)
async def get_image_storage_status(
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await ImageService.get_storage_status(image_id, db)


@router.get(
    "/{image_id}/preview",
    summary="Download Browser-Friendly Preview",
    description="Returns the rendered, normalized, downsampled PNG preview of the satellite image."
)
async def get_image_preview(
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    preview_bytes, mime = await ImageService.get_preview_bytes(image_id, db)
    return Response(
        content=preview_bytes,
        media_type=mime,
        headers={"Cache-Control": "public, max-age=86400"}
    )


@router.delete(
    "/{image_id}",
    summary="Delete Image",
    description="Permanently deletes the image record, raw raster object, and preview cache."
)
async def delete_image(
    image_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    await ImageService.delete_image(image_id, db)
    return {"id": image_id, "deleted": True, "message": "Image deleted successfully."}
