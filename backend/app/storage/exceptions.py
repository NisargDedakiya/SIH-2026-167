"""
Storage exceptions for SatQuery raster object persistence and integrity checks.
"""

from typing import Optional


class StorageError(Exception):
    """Base exception for object storage operations."""
    pass


class StorageObjectNotFoundError(StorageError):
    """
    Raised when an image or pair is registered in the database,
    but its backing raster object (original.tif or preview.png) is missing from object storage.
    """

    def __init__(
        self,
        message: str,
        image_id: Optional[str] = None,
        object_key: Optional[str] = None,
        storage_status: str = "MISSING"
    ):
        super().__init__(message)
        self.code = "IMAGE_OBJECT_MISSING"
        self.message = message
        self.image_id = str(image_id) if image_id else None
        self.object_key = object_key
        self.storage_status = storage_status
