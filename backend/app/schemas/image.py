from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class BoundingBoxSchema(BaseModel):
    left: float
    bottom: float
    right: float
    top: float


class ResolutionSchema(BaseModel):
    x: float
    y: float


class RasterMetadataSchema(BaseModel):
    width: int
    height: int
    bands: int
    dtype: str
    nodata: Optional[float] = None


class GeospatialMetadataSchema(BaseModel):
    is_geospatial: bool
    crs: Optional[str] = None
    epsg: Optional[int] = None
    bounds: Optional[BoundingBoxSchema] = None
    resolution: Optional[ResolutionSchema] = None
    transform: Optional[List[float]] = None


class ValidationResultSchema(BaseModel):
    valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ImageUploadResponse(BaseModel):
    id: uuid.UUID
    filename: str
    status: str
    message: str


class ImageInspectResponse(BaseModel):
    id: uuid.UUID
    filename: str
    format: str
    size_bytes: int
    modality: str = "unknown"
    raster: RasterMetadataSchema
    geospatial: GeospatialMetadataSchema
    validation: ValidationResultSchema


class ImageValidationResponse(BaseModel):
    valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Optional[ImageInspectResponse] = None
