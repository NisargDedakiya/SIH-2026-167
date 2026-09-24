from dataclasses import dataclass
import io
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image

from app.core.config import get_settings
from .reader import SafeRasterReader
from .normalization import normalize_raster_band

settings = get_settings()


@dataclass
class PreviewOutput:
    image_bytes: bytes
    mime_type: str
    width: int
    height: int
    selected_bands: List[int]
    normalization_method: str = "percentile_2_98"


class PreviewGenerator:
    """Generates downsampled, normalized browser-friendly RGB previews."""

    @classmethod
    def generate(
        cls,
        file_bytes: bytes,
        max_dim: Optional[int] = None,
        nodata: Optional[float] = None
    ) -> PreviewOutput:
        limit = max_dim or settings.PREVIEW_MAX_SIZE

        # 1. Read downsampled bands safely
        bands_data, orig_size = SafeRasterReader.read_downsampled_bands(
            file_bytes=file_bytes,
            max_dim=limit
        )

        num_bands, h, w = bands_data.shape

        selected_bands: List[int] = []

        if num_bands >= 3:
            # Multi-band raster: use first 3 bands as RGB (or bands 3, 2, 1 if common optical)
            # Default to bands 1, 2, 3 for general rasters
            selected_bands = [1, 2, 3]
            r = normalize_raster_band(bands_data[0], nodata=nodata)
            g = normalize_raster_band(bands_data[1], nodata=nodata)
            b = normalize_raster_band(bands_data[2], nodata=nodata)
            rgb = np.stack([r, g, b], axis=-1)
        elif num_bands == 2:
            selected_bands = [1, 2]
            b1 = normalize_raster_band(bands_data[0], nodata=nodata)
            b2 = normalize_raster_band(bands_data[1], nodata=nodata)
            # Duplicate first band for 3rd channel
            rgb = np.stack([b1, b2, b1], axis=-1)
        else:
            # Single band (grayscale or SAR amplitude / elevation)
            selected_bands = [1]
            gray = normalize_raster_band(bands_data[0], nodata=nodata)
            rgb = np.stack([gray, gray, gray], axis=-1)

        # 2. Encode to PNG
        img = Image.fromarray(rgb, mode="RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        preview_bytes = buf.getvalue()

        return PreviewOutput(
            image_bytes=preview_bytes,
            mime_type="image/png",
            width=img.width,
            height=img.height,
            selected_bands=selected_bands,
            normalization_method="percentile_2_98"
        )
