"""
Alignment & Co-Registration Engine for Bi-Temporal Change Detection.
Aligns T2 raster into T1's pixel grid and geospatial coordinate reference frame
without modifying the original satellite images.
"""

import io
from typing import Any, Dict, Optional, Tuple
import numpy as np
from PIL import Image
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.warp import reproject

from app.core.logging import logger
from app.database.models import ImageModel


class AlignmentEngine:
    """
    Performs non-destructive spatial co-registration between T1 (reference) and T2 (target) rasters.
    """

    @classmethod
    def align_pair(
        cls,
        image_t1: ImageModel,
        image_t2: ImageModel,
        t1_bytes: bytes,
        t2_bytes: bytes
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Co-registers T2 into T1's grid dimensions and CRS.
        Returns:
            (t1_array, aligned_t2_array, alignment_metadata)
            where arrays are normalized RGB [0..255] uint8 arrays of shape (H, W, 3).
        """
        meta: Dict[str, Any] = {
            "status": "NOT_REQUIRED",
            "method": "none",
            "source_crs": image_t2.crs,
            "target_crs": image_t1.crs,
            "target_width": image_t1.width,
            "target_height": image_t1.height,
            "resampling": "bilinear",
        }

        # 1. Read T1 into normalized RGB array
        t1_array = cls._bytes_to_rgb_array(t1_bytes)
        target_h, target_w = t1_array.shape[:2]

        # 2. Check if both are georeferenced and need reprojection
        if image_t1.is_geospatial and image_t2.is_geospatial and image_t1.crs and image_t2.crs:
            try:
                aligned_t2_array, reproj_meta = cls._reproject_geospatial(
                    t1_bytes=t1_bytes,
                    t2_bytes=t2_bytes,
                    image_t1=image_t1,
                    image_t2=image_t2
                )
                meta.update(reproj_meta)
                return t1_array, aligned_t2_array, meta
            except Exception as e:
                logger.warning(f"Geospatial reprojection failed: {e}. Falling back to image-space resampling.")

        # 3. Image-space resampling / dimension matching
        t2_array = cls._bytes_to_rgb_array(t2_bytes)
        t2_h, t2_w = t2_array.shape[:2]

        if t2_w == target_w and t2_h == target_h:
            meta["status"] = "NOT_REQUIRED"
            meta["method"] = "identical_dimensions"
            return t1_array, t2_array, meta

        # Resample T2 to match T1 dimensions
        meta["status"] = "RESAMPLED"
        meta["method"] = "bilinear_resampling"
        meta["original_t2_dims"] = [t2_w, t2_h]

        t2_pil = Image.fromarray(t2_array)
        t2_resampled = t2_pil.resize((target_w, target_h), Image.Resampling.BILINEAR)
        aligned_t2_array = np.array(t2_resampled)

        return t1_array, aligned_t2_array, meta

    @classmethod
    def _reproject_geospatial(
        cls,
        t1_bytes: bytes,
        t2_bytes: bytes,
        image_t1: ImageModel,
        image_t2: ImageModel
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reprojects T2 dataset into T1's transform, CRS, width, and height using rasterio."""
        with MemoryFile(t1_bytes) as mem_t1, MemoryFile(t2_bytes) as mem_t2:
            with mem_t1.open() as ds_t1, mem_t2.open() as ds_t2:
                target_crs = ds_t1.crs
                target_transform = ds_t1.transform
                target_w = ds_t1.width
                target_h = ds_t1.height
                bands_count = min(3, ds_t2.count)

                # Destination buffer for T2
                dest_data = np.zeros((bands_count, target_h, target_w), dtype=np.float32)

                for band_idx in range(1, bands_count + 1):
                    reproject(
                        source=rasterio.band(ds_t2, band_idx),
                        destination=dest_data[band_idx - 1],
                        src_transform=ds_t2.transform,
                        src_crs=ds_t2.crs,
                        dst_transform=target_transform,
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear,
                    )

                # Normalize to uint8 RGB
                aligned_rgb = cls._multiband_to_uint8(dest_data)

                reproj_meta = {
                    "status": "REPROJECTED",
                    "method": "rasterio_warp_reproject",
                    "source_crs": str(ds_t2.crs),
                    "target_crs": str(target_crs),
                    "resampling": "bilinear",
                }
                return aligned_rgb, reproj_meta

    @classmethod
    def _bytes_to_rgb_array(cls, image_bytes: bytes) -> np.ndarray:
        """Decodes raw raster bytes to an 8-bit RGB array [H, W, 3]."""
        try:
            with MemoryFile(image_bytes) as mem:
                with mem.open() as ds:
                    data = ds.read([1, 2, 3] if ds.count >= 3 else [1] * 3)
                    return cls._multiband_to_uint8(data)
        except Exception:
            pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return np.array(pil_img, dtype=np.uint8)

    @classmethod
    def _multiband_to_uint8(cls, data: np.ndarray) -> np.ndarray:
        """Normalizes float/uint16 band data [3, H, W] to uint8 [H, W, 3]."""
        out = np.zeros((data.shape[1], data.shape[2], 3), dtype=np.uint8)
        for i in range(min(3, data.shape[0])):
            band = data[i].astype(np.float32)
            valid = np.isfinite(band)
            if np.any(valid):
                min_v = np.percentile(band[valid], 2)
                max_v = np.percentile(band[valid], 98)
                if max_v > min_v:
                    scaled = np.clip((band - min_v) / (max_v - min_v) * 255.0, 0, 255)
                    out[:, :, i] = scaled.astype(np.uint8)
                else:
                    out[:, :, i] = np.clip(band, 0, 255).astype(np.uint8)
        return out
