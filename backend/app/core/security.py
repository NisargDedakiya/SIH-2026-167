import re
import uuid
from pathlib import Path
from typing import Tuple

ALLOWED_EXTENSIONS = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}

# Magic byte signatures for remote-sensing raster & standard image formats
MAGIC_SIGNATURES = {
    # TIFF little-endian (Intel)
    b"II*\x00": "TIFF",
    # TIFF big-endian (Motorola)
    b"MM\x00*": "TIFF",
    # BigTIFF little-endian
    b"II+\x00": "BigTIFF",
    # BigTIFF big-endian
    b"MM\x00+": "BigTIFF",
    # PNG standard header
    b"\x89PNG\r\n\x1a\n": "PNG",
    # JPEG start-of-image
    b"\xff\xd8\xff": "JPEG",
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize client-provided filename to prevent path traversal,
    null byte injection, or malicious characters.
    """
    if not filename:
        return "unnamed_image"

    # Strip directory components (path traversal prevention)
    clean_name = Path(filename).name
    # Remove null bytes and non-printable characters
    clean_name = re.sub(r"[\x00-\x1f\x7f]", "", clean_name)
    # Allow alphanumeric, dashes, underscores, and dots
    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", clean_name)
    # Deduplicate dots and slashes
    clean_name = re.sub(r"\.{2,}", ".", clean_name)

    return clean_name.strip("._") or "unnamed_image"


def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """Check if file extension matches supported remote-sensing formats."""
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_EXTENSIONS:
        return True, ext
    return False, ext


def inspect_magic_bytes(header_bytes: bytes) -> Tuple[bool, str]:
    """
    Inspect raw initial bytes to ensure binary payload corresponds
    to legitimate TIFF, PNG, or JPEG raster streams.
    """
    for sig, fmt in MAGIC_SIGNATURES.items():
        if header_bytes.startswith(sig):
            return True, fmt
    return False, "UNKNOWN"


def generate_storage_keys(image_id: uuid.UUID, extension: str) -> Tuple[str, str]:
    """
    Generate randomized, isolated storage keys.
    Prevents path traversal and predictable filesystem access.
    Returns (original_object_key, preview_object_key).
    """
    clean_ext = extension.lstrip(".").lower()
    if clean_ext == "jpeg":
        clean_ext = "jpg"
    elif clean_ext == "tiff":
        clean_ext = "tif"

    orig_key = f"images/{image_id}/original.{clean_ext}"
    preview_key = f"images/{image_id}/preview.png"
    return orig_key, preview_key
