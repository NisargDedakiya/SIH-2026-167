"""
Visual Evidence Overlay and Crop Rendering Engine for Remote-Sensing Grounding.
Produces high-contrast visual artifacts for SIH demonstration and geospatial verification.
"""

import io
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFont

# Color palette mapped by semantic categories
COLOR_PALETTE = {
    "water": (6, 182, 212),       # Cyan-500
    "river": (14, 165, 233),      # Sky-500
    "lake": (59, 130, 246),       # Blue-500
    "building": (245, 158, 11),   # Amber-500
    "urban": (234, 88, 12),       # Orange-600
    "structure": (249, 115, 22),  # Orange-500
    "forest": (16, 185, 129),     # Emerald-500
    "tree": (34, 197, 94),        # Green-500
    "vegetation": (22, 163, 74),  # Green-600
    "agriculture": (132, 204, 22),# Lime-500
    "road": (168, 85, 247),       # Purple-500
    "runway": (236, 72, 153),     # Pink-500
    "default": (6, 182, 212),     # Cyan
}


def get_color_for_label(label: str) -> Tuple[int, int, int]:
    """Selects a distinctive theme color based on semantic keyword match."""
    label_lower = label.lower()
    for key, color in COLOR_PALETTE.items():
        if key in label_lower:
            return color
    return COLOR_PALETTE["default"]


def render_evidence_overlay(
    base_image: Image.Image,
    regions: List[Dict[str, Any]],
    fill_alpha: int = 55
) -> Image.Image:
    """
    Renders visual bounding box overlays with translucent interior fills,
    crisp outer boundaries, and formatted label/confidence pills.
    """
    # Work on an RGBA copy for clean alpha blending
    img_rgba = base_image.convert("RGBA")
    overlay = Image.new("RGBA", img_rgba.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    width, height = img_rgba.size

    for region in regions:
        pixel_geo = region.get("pixel_geometry") or region.get("pixel_coords") or {}
        x1 = pixel_geo.get("x1", 0)
        y1 = pixel_geo.get("y1", 0)
        x2 = pixel_geo.get("x2", 0)
        y2 = pixel_geo.get("y2", 0)
        label = region.get("label", "Region")
        conf = region.get("confidence", 0.0)

        color_rgb = get_color_for_label(label)
        fill_color = (*color_rgb, fill_alpha)
        border_color = (*color_rgb, 240)

        # 1. Draw translucent bounding box fill
        draw.rectangle([x1, y1, x2, y2], fill=fill_color, outline=None)

        # 2. Draw solid multi-pixel border
        border_width = max(2, min(6, int(width / 300)))
        for i in range(border_width):
            draw.rectangle(
                [x1 + i, y1 + i, x2 - i, y2 - i],
                outline=border_color
            )

        # 3. Draw high-contrast header label pill
        label_text = f"{label.upper()} {int(conf * 100)}%"
        # Calculate approximate text bounds
        char_w = 7
        char_h = 13
        text_w = len(label_text) * char_w + 12
        text_h = char_h + 8

        pill_y1 = max(0, y1 - text_h)
        pill_y2 = pill_y1 + text_h
        pill_x1 = x1
        pill_x2 = min(width, x1 + text_w)

        draw.rectangle([pill_x1, pill_y1, pill_x2, pill_y2], fill=border_color)
        draw.text(
            (pill_x1 + 6, pill_y1 + 4),
            label_text,
            fill=(255, 255, 255, 255)
        )

    # Blend overlay with original
    composited = Image.alpha_composite(img_rgba, overlay)
    return composited.convert("RGB")


def render_region_crop(
    base_image: Image.Image,
    pixel_bbox: Dict[str, int],
    padding_pct: float = 0.1
) -> Image.Image:
    """
    Extracts a high-resolution crop of a specific visual evidence region
    with contextual padding.
    """
    width, height = base_image.size
    x1 = pixel_bbox["x1"]
    y1 = pixel_bbox["y1"]
    x2 = pixel_bbox["x2"]
    y2 = pixel_bbox["y2"]

    pad_w = int((x2 - x1) * padding_pct)
    pad_h = int((y2 - y1) * padding_pct)

    crop_x1 = max(0, x1 - pad_w)
    crop_y1 = max(0, y1 - pad_h)
    crop_x2 = min(width, x2 + pad_w)
    crop_y2 = min(height, y2 + pad_h)

    return base_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))


def image_to_png_bytes(img: Image.Image) -> bytes:
    """Serializes PIL image to PNG bytes."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
