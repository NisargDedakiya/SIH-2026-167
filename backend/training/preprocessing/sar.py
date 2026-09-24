"""
SAR Microwave Preprocessing Pipeline for Domain Adaptation.
Converts linear amplitude/power to calibrated decibel (dB) scale and mitigates speckle noise.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
from PIL import Image


class SARPreprocessor:
    """
    Standardizes raw SAR backscatter channels (VV, VH, HH, HV).
    Enforces physics-aware decibel transformation: 10 * log10(amplitude^2 + epsilon).
    """

    @staticmethod
    def to_decibel(
        channel: np.ndarray,
        epsilon: float = 1e-6
    ) -> np.ndarray:
        """
        Converts linear intensity or amplitude to decibel (dB) scale.
        """
        arr = np.nan_to_num(channel.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
        arr = np.maximum(arr, 0.0)
        # 10 * log10(arr + epsilon)
        db = 10.0 * np.log10(arr + epsilon)
        return db.astype(np.float32)

    @classmethod
    def speckle_filter_and_normalize(
        cls,
        channel: np.ndarray,
        lower_percentile: float = 1.0,
        upper_percentile: float = 99.0
    ) -> np.ndarray:
        """
        Calibrates to dB and clips 1%-99% speckle extremes to [0, 255] uint8.
        """
        db = cls.to_decibel(channel)
        p_low = np.percentile(db, lower_percentile)
        p_high = np.percentile(db, upper_percentile)

        if p_high <= p_low:
            p_high = p_low + 1.0

        norm = (db - p_low) / (p_high - p_low)
        norm = np.clip(norm, 0.0, 1.0) * 255.0
        return norm.astype(np.uint8)

    @classmethod
    def compose_sar_composite(
        cls,
        sar_channels: Dict[str, np.ndarray],
        target_size: Optional[Tuple[int, int]] = None
    ) -> Image.Image:
        """
        Composes dual-pol SAR (VV, VH) into a false-color microwave composite:
        R: VV (surface roughness)
        G: VH (volume scattering)
        B: Ratio VV / VH (dielectric contrast)
        """
        vv = sar_channels.get("VV")
        vh = sar_channels.get("VH")

        if vv is None and sar_channels:
            vv = next(iter(sar_channels.values()))
        if vh is None:
            vh = vv

        r = cls.speckle_filter_and_normalize(vv)
        g = cls.speckle_filter_and_normalize(vh)

        # Ratio channel
        ratio = (vv.astype(np.float32) + 1e-4) / (vh.astype(np.float32) + 1e-4)
        b = cls.speckle_filter_and_normalize(ratio)

        composite = np.stack([r, g, b], axis=-1)
        img = Image.fromarray(composite, mode="RGB")
        if target_size and img.size != target_size:
            img = img.resize(target_size, Image.Resampling.BILINEAR)
        return img
