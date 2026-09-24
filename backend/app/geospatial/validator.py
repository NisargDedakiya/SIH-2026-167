from dataclasses import dataclass, field
import io
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image

from app.core.config import get_settings
from app.core.security import inspect_magic_bytes, validate_file_extension
from app.core.logging import logger

settings = get_settings()


@dataclass
class ValidationResult:
    valid: bool
    format_name: str
    is_geospatial: bool = False
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class GeospatialValidator:
    """Multi-tiered validator for satellite and standard imagery."""

    @classmethod
    def validate_pre_upload(cls, filename: str, content_length: Optional[int]) -> Tuple[bool, List[str]]:
        """Fast pre-flight validation on filename and declared content length."""
        errors = []
        is_allowed, ext = validate_file_extension(filename)
        if not is_allowed:
            errors.append(f"Unsupported file extension '{ext}'. Allowed extensions: .tif, .tiff, .png, .jpg, .jpeg")

        if content_length is not None and content_length > settings.max_upload_size_bytes:
            errors.append(
                f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        return len(errors) == 0, errors

    @classmethod
    def validate_file_content(cls, file_bytes: bytes, filename: str) -> ValidationResult:
        """Deep validation of raw file bytes, magic headers, and raster parseability."""
        result = ValidationResult(valid=False, format_name="UNKNOWN")

        # 1. Size check
        if len(file_bytes) > settings.max_upload_size_bytes:
            result.errors.append(
                f"File payload ({len(file_bytes) / (1024 * 1024):.1f} MB) exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )
            return result

        if len(file_bytes) < 16:
            result.errors.append("File is empty or too small to contain valid raster headers.")
            return result

        # 2. Extension check
        is_allowed_ext, ext = validate_file_extension(filename)
        if not is_allowed_ext:
            result.errors.append(f"Disallowed file extension '{ext}'.")
            return result

        # 3. Magic byte signature check
        is_magic_valid, detected_fmt = inspect_magic_bytes(file_bytes[:16])
        if not is_magic_valid:
            result.errors.append(
                "File header does not match any recognized remote-sensing or image format (magic byte mismatch)."
            )
            return result

        # 4. Raster structure validation
        if detected_fmt in ["TIFF", "BigTIFF"]:
            cls._validate_tiff(file_bytes, result)
        elif detected_fmt in ["PNG", "JPEG"]:
            cls._validate_standard_image(file_bytes, detected_fmt, result)

        return result

    MAX_RASTER_DIMENSION = 8192
    MAX_RASTER_PIXELS = 8192 * 8192

    @classmethod
    def _validate_tiff(cls, file_bytes: bytes, result: ValidationResult):
        """Validate TIFF/GeoTIFF raster integrity using rasterio with decompression bomb protection."""
        import rasterio
        from rasterio.io import MemoryFile

        try:
            with MemoryFile(file_bytes) as memfile:
                with memfile.open() as dataset:
                    result.format_name = "GeoTIFF" if (dataset.crs or dataset.transform != rasterio.Affine.identity()) else "TIFF"
                    
                    if dataset.width <= 0 or dataset.height <= 0:
                        result.errors.append("TIFF contains invalid raster dimensions (zero or negative).")
                        return

                    if dataset.width > cls.MAX_RASTER_DIMENSION or dataset.height > cls.MAX_RASTER_DIMENSION:
                        result.errors.append(
                            f"TIFF raster dimensions ({dataset.width}x{dataset.height}) exceed maximum allowable limit of {cls.MAX_RASTER_DIMENSION}px (resource protection)."
                        )
                        return

                    if (dataset.width * dataset.height) > cls.MAX_RASTER_PIXELS:
                        result.errors.append(
                            f"TIFF total pixel count exceeds maximum allowable limit of {cls.MAX_RASTER_PIXELS} pixels (decompression protection)."
                        )
                        return

                    if dataset.count <= 0:
                        result.errors.append("TIFF contains no raster bands.")
                        return

                    if dataset.crs:
                        result.is_geospatial = True
                    else:
                        result.is_geospatial = False
                        result.warnings.append(
                            "TIFF is valid but does not contain geospatial referencing (missing CRS/geotransform)."
                        )

                    result.valid = True

        except rasterio.RasterioIOError as e:
            logger.warning(f"Corrupted TIFF encountered: {e}")
            result.errors.append(f"Corrupted or malformed TIFF raster: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error validating TIFF: {e}")
            result.errors.append(f"Raster read failure: {str(e)}")

    @classmethod
    def _validate_standard_image(cls, file_bytes: bytes, detected_fmt: str, result: ValidationResult):
        """Validate standard image (PNG/JPEG) integrity with decompression bomb protection."""
        try:
            Image.MAX_IMAGE_PIXELS = cls.MAX_RASTER_PIXELS
            with Image.open(io.BytesIO(file_bytes)) as img:
                if img.width > cls.MAX_RASTER_DIMENSION or img.height > cls.MAX_RASTER_DIMENSION:
                    result.errors.append(
                        f"Image dimensions ({img.width}x{img.height}) exceed maximum allowable limit of {cls.MAX_RASTER_DIMENSION}px."
                    )
                    return
                img.verify()  # Fast structural verification

            result.format_name = detected_fmt
            result.is_geospatial = False  # PNG/JPEG default non-geospatial per specifications
            result.valid = True

        except Exception as e:
            logger.warning(f"Corrupted image file: {e}")
            result.errors.append(f"Corrupted image file: {str(e)}")
