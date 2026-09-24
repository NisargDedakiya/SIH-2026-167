import io
import math
from typing import Optional, Tuple
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.windows import Window
from PIL import Image

from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


class SafeRasterReader:
    """
    Safely reads satellite rasters and standard images without memory bloat.
    Applies downsampling factors and windowed block reads.
    """

    @classmethod
    def read_downsampled_bands(
        cls,
        file_bytes: bytes,
        max_dim: int = 2048,
        selected_bands: Optional[Tuple[int, ...]] = None
    ) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Read raster data scaled down to fit within max_dim x max_dim.
        Returns (bands_array, (original_width, original_height)).
        Shape of bands_array: (bands, height, width).
        """
        try:
            with MemoryFile(file_bytes) as memfile:
                with memfile.open() as dataset:
                    orig_w = dataset.width
                    orig_h = dataset.height

                    # Determine downsampling decimation factor
                    max_orig = max(orig_w, orig_h)
                    if max_orig > max_dim:
                        scale = max_dim / max_orig
                        out_w = max(1, int(orig_w * scale))
                        out_h = max(1, int(orig_h * scale))
                    else:
                        out_w = orig_w
                        out_h = orig_h

                    # Determine bands to read
                    total_bands = dataset.count
                    if selected_bands:
                        bands_to_read = [b for b in selected_bands if 1 <= b <= total_bands]
                    else:
                        bands_to_read = list(range(1, total_bands + 1))

                    if not bands_to_read:
                        bands_to_read = [1]

                    # Perform decimated/windowed read using nearest or bilinear
                    data = dataset.read(
                        bands_to_read,
                        out_shape=(len(bands_to_read), out_h, out_w),
                        resampling=Resampling.bilinear
                    )
                    return data, (orig_w, orig_h)

        except (rasterio.RasterioIOError, Exception) as e:
            # Fallback for standard images via Pillow
            return cls._read_pillow_downsampled(file_bytes, max_dim)

    @classmethod
    def _read_pillow_downsampled(cls, file_bytes: bytes, max_dim: int) -> Tuple[np.ndarray, Tuple[int, int]]:
        with Image.open(io.BytesIO(file_bytes)) as img:
            orig_w, orig_h = img.size

            if max(orig_w, orig_h) > max_dim:
                img.thumbnail((max_dim, max_dim), Image.Resampling.BILINEAR)

            # Convert to RGB if palette or non-standard
            if img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGB")

            arr = np.array(img)
            if arr.ndim == 2:
                # 1 band (height, width) -> (1, height, width)
                arr = arr[np.newaxis, ...]
            elif arr.ndim == 3:
                # (height, width, channels) -> (channels, height, width)
                arr = np.transpose(arr, (2, 0, 1))

            return arr, (orig_w, orig_h)
