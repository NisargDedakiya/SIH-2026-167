"""
SatQuery AI — Storage Integrity Verification Utility.

Audits database records against backing object storage:
- Scans all ImageModel records in the database.
- Checks physical existence of object_key (original GeoTIFF).
- Checks physical existence of preview_key (rendered PNG preview).
- Detects orphaned files in local storage / MinIO.
- Outputs standardized health summary without deleting any records or files.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.database.models import ImageModel
from app.database.session import async_session_factory
from app.storage.object_store import get_object_store
from app.core.config import get_settings


async def verify_integrity():
    settings = get_settings()
    store = get_object_store()

    async with async_session_factory() as session:
        stmt = select(ImageModel)
        result = await session.execute(stmt)
        images = result.scalars().all()

    total_images = len(images)
    avail_orig = 0
    missing_orig = 0
    avail_preview = 0
    missing_preview = 0
    broken_records = 0

    broken_ids = []

    for img in images:
        is_broken = False

        # Check original raster
        if img.object_key and await store.exists(img.object_key):
            avail_orig += 1
        else:
            missing_orig += 1
            is_broken = True

        # Check preview
        if img.preview_key:
            if await store.exists(img.preview_key):
                avail_preview += 1
            else:
                missing_preview += 1
                is_broken = True
        else:
            missing_preview += 1

        if is_broken:
            broken_records += 1
            broken_ids.append((str(img.id), img.original_filename or "unnamed", img.object_key))

    # Check for orphaned files in local storage if using local backend
    orphaned_count = 0
    if settings.STORAGE_BACKEND.lower() == "local":
        local_base = Path(settings.LOCAL_STORAGE_PATH).resolve()
        if local_base.exists():
            known_keys = {
                Path(img.object_key).resolve() for img in images if img.object_key
            } | {
                Path(img.preview_key).resolve() for img in images if img.preview_key
            }
            # Scan files
            for root, _, files in os.walk(local_base):
                for f in files:
                    file_path = Path(root) / f
                    if file_path.resolve() not in known_keys:
                        orphaned_count += 1

    print("=" * 50)
    print("SATQUERY STORAGE INTEGRITY")
    print("=" * 50)
    print(f"Database images:\n  {total_images}")
    print("Original objects:")
    print(f"  Available: {avail_orig}")
    print(f"  Missing: {missing_orig}")
    print("Preview objects:")
    print(f"  Available: {avail_preview}")
    print(f"  Missing: {missing_preview}")
    print(f"Broken image records:\n  {broken_records}")
    if orphaned_count > 0:
        print(f"Orphaned storage files:\n  {orphaned_count}")
    print("=" * 50)

    if broken_records > 0 and len(broken_ids) <= 10:
        print("\nSample broken image IDs:")
        for bid, bname, bkey in broken_ids[:10]:
            print(f"  - {bid} ({bname}): {bkey}")
    elif broken_records > 10:
        print(f"\nShowing first 10 of {broken_records} broken image IDs:")
        for bid, bname, bkey in broken_ids[:10]:
            print(f"  - {bid} ({bname}): {bkey}")

    return {
        "total_images": total_images,
        "available_originals": avail_orig,
        "missing_originals": missing_orig,
        "available_previews": avail_preview,
        "missing_previews": missing_preview,
        "broken_records": broken_records,
        "orphaned_files": orphaned_count
    }


def main():
    asyncio.run(verify_integrity())


if __name__ == "__main__":
    main()
