"""
Change Map representation and utilities.
Normalizes pixel-level difference masks, calculates statistical metrics,
and renders visual difference overlay artifacts.
"""

import io
from typing import Any, Dict, Optional, Tuple
import numpy as np
from PIL import Image


class ChangeMap:
    """
    Standardized spatial change map representation across bi-temporal remote-sensing rasters.
    """

    def __init__(
        self,
        change_mask: np.ndarray,
        change_scores: Optional[np.ndarray] = None,
        threshold: float = 0.35,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        change_mask: 2D boolean or integer (0 or 1) array of shape (H, W).
        change_scores: optional continuous confidence array [0.0..1.0] of shape (H, W).
        """
        self.mask = (change_mask > 0).astype(np.uint8)
        self.height, self.width = self.mask.shape
        self.threshold = threshold
        self.metadata = metadata or {}

        if change_scores is not None:
            self.scores = np.clip(change_scores, 0.0, 1.0)
        else:
            self.scores = self.mask.astype(np.float32)

    @property
    def total_pixels(self) -> int:
        return self.width * self.height

    @property
    def changed_pixels(self) -> int:
        return int(np.sum(self.mask))

    @property
    def change_percentage(self) -> float:
        if self.total_pixels == 0:
            return 0.0
        return round((self.changed_pixels / self.total_pixels) * 100.0, 2)

    @property
    def has_change(self) -> bool:
        return self.changed_pixels > 0

    @property
    def mean_change_confidence(self) -> float:
        if self.changed_pixels == 0:
            return 0.0
        return float(np.mean(self.scores[self.mask == 1]))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "total_pixels": self.total_pixels,
            "changed_pixels": self.changed_pixels,
            "change_percentage": self.change_percentage,
            "mean_confidence": round(self.mean_change_confidence, 4),
            "threshold": self.threshold,
        }

    def render_overlay_image(self, base_rgb: np.ndarray, alpha: float = 0.45) -> Image.Image:
        """
        Blends the change mask (red/amber highlight) over the base RGB array.
        """
        h, w = base_rgb.shape[:2]
        base_pil = Image.fromarray(base_rgb).convert("RGBA")

        # Color map: highlighted changed pixels in vibrant crimson/amber (244, 63, 94)
        overlay_arr = np.zeros((h, w, 4), dtype=np.uint8)
        mask_bool = self.mask == 1

        # Red tint for change
        overlay_arr[mask_bool, 0] = 239  # R
        overlay_arr[mask_bool, 1] = 68   # G
        overlay_arr[mask_bool, 2] = 68   # B
        overlay_arr[mask_bool, 3] = int(255 * alpha)  # Alpha

        overlay_pil = Image.fromarray(overlay_arr, mode="RGBA")
        blended = Image.alpha_composite(base_pil, overlay_pil).convert("RGB")
        return blended

    def to_png_bytes(self, base_rgb: Optional[np.ndarray] = None) -> bytes:
        """Returns PNG bytes of the change overlay or binary change mask."""
        if base_rgb is not None:
            img = self.render_overlay_image(base_rgb)
        else:
            # Standalone visual mask (white = change, black = background)
            mask_rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            mask_rgb[self.mask == 1] = [239, 68, 68]
            img = Image.fromarray(mask_rgb)

        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
