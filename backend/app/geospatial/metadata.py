from dataclasses import dataclass, field
import io
from typing import Any, Dict, List, Optional
from PIL import Image
import rasterio
from rasterio.io import MemoryFile

from app.core.logging import logger


@dataclass
class ExtractedMetadata:
    width: int
    height: int
    bands: int
    dtype: str
    nodata: Optional[float]
    format_name: str
    is_geospatial: bool
    crs_str: Optional[str] = None
    epsg_code: Optional[int] = None
    resolution_x: Optional[float] = None
    resolution_y: Optional[float] = None
    bounds: Optional[Dict[str, float]] = None
    transform: Optional[List[float]] = None
    sensor: Optional[str] = None
    modality: str = "unknown"
    warnings: List[str] = field(default_factory=list)


class MetadataExtractor:
    """Extracts raster and geospatial technical metadata from raw imagery."""

    @classmethod
    def extract(cls, file_bytes: bytes, filename: str) -> ExtractedMetadata:
        # Check if TIFF/GeoTIFF
        try:
            with MemoryFile(file_bytes) as memfile:
                with memfile.open() as ds:
                    return cls._extract_rasterio(ds)
        except Exception:
            # Fall back to Pillow for PNG/JPEG
            return cls._extract_pillow(file_bytes, filename)

    @classmethod
    def _extract_rasterio(cls, ds: rasterio.io.DatasetReader) -> ExtractedMetadata:
        warnings = []
        is_geo = False
        crs_str = None
        epsg = None
        bounds_dict = None
        res_x = None
        res_y = None
        transform_list = None

        if ds.crs:
            is_geo = True
            crs_str = ds.crs.to_string()
            epsg = ds.crs.to_epsg()

            b = ds.bounds
            bounds_dict = {
                "left": float(b.left),
                "bottom": float(b.bottom),
                "right": float(b.right),
                "top": float(b.top),
            }

            res_x = float(ds.res[0])
            res_y = float(ds.res[1])

            # Convert 3x3 affine matrix to 6 coefficients
            t = ds.transform
            transform_list = [t.a, t.b, t.c, t.d, t.e, t.f]
        else:
            is_geo = False
            if ds.driver in ("GTiff", "TIFF"):
                warnings.append("TIFF is valid but does not contain geospatial referencing.")

        # Assign format based on GDAL driver
        driver = getattr(ds, "driver", "")
        if driver == "GTiff":
            format_name = "GeoTIFF" if is_geo else "TIFF"
        elif driver == "PNG":
            format_name = "PNG"
            is_geo = False  # Per spec, standard PNGs are not geospatial
        elif driver in ("JPEG", "JPG"):
            format_name = "JPEG"
            is_geo = False
        else:
            format_name = "GeoTIFF" if is_geo else "TIFF"

        # Modality inference: if 4+ bands or tags specify
        modality = "unknown"
        if ds.count >= 4:
            modality = "multispectral"
        elif ds.count == 3:
            modality = "optical"
        elif ds.count == 1:
            modality = "unknown"  # could be panchromatic, SAR, or elevation

        return ExtractedMetadata(
            width=ds.width,
            height=ds.height,
            bands=ds.count,
            dtype=str(ds.dtypes[0]),
            nodata=float(ds.nodata) if ds.nodata is not None else None,
            format_name=format_name,
            is_geospatial=is_geo,
            crs_str=crs_str,
            epsg_code=epsg,
            resolution_x=res_x,
            resolution_y=res_y,
            bounds=bounds_dict,
            transform=transform_list,
            modality=modality,
            warnings=warnings
        )

    @classmethod
    def _extract_pillow(cls, file_bytes: bytes, filename: str) -> ExtractedMetadata:
        with Image.open(io.BytesIO(file_bytes)) as img:
            bands = len(img.getbands()) if hasattr(img, "getbands") else 1
            fmt = img.format or "JPEG"
            if fmt == "PNG":
                format_name = "PNG"
            elif fmt in ("JPEG", "JPG"):
                format_name = "JPEG"
            else:
                format_name = fmt

            # Modality estimation
            modality = "optical" if bands in (3, 4) else "unknown"

            return ExtractedMetadata(
                width=img.width,
                height=img.height,
                bands=bands,
                dtype="uint8",
                nodata=None,
                format_name=format_name,
                is_geospatial=False,
                crs_str=None,
                epsg_code=None,
                resolution_x=None,
                resolution_y=None,
                bounds=None,
                transform=None,
                modality=modality,
                warnings=[]
            )
