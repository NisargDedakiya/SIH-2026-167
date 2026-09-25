"""
SatQuery AI — Seed & Repair Demo Assets Utility.

Ingests official demo GeoTIFFs from demo/ into the database and object storage:
- Demo 1 & Demo 2: Single Image & Visual Grounding (demo/grounding/image.tif)
- Demo 3: Bi-Temporal Change Detection (demo/temporal/t1.tif, demo/temporal/t2.tif)
- Demo 4: Cross-Modal Optical-SAR Fusion (demo/optical_sar/optical.tif, demo/optical_sar/sar.tif)

Ensures that:
1. Both database records AND backing storage files (original.tif, preview.png) exist.
2. BiTemporalPair and OpticalSARPair are registered and verified.
3. Zero missing storage errors occur during live SIH demonstrations.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
repo_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database.session import async_session_factory, init_db
from app.services.image_service import ImageService
from app.temporal.service import get_temporal_service
from app.temporal.schemas import BiTemporalPairCreate
from app.cross_modal.service import get_cross_modal_service
from app.cross_modal.schemas import OpticalSARPairCreate
from app.core.logging import logger


async def seed_demo_assets():
    print("=" * 60)
    print("SatQuery AI — Seeding & Repairing Demo Assets")
    print("=" * 60)

    demo_dir = repo_root / "demo"
    if not demo_dir.exists():
        print(f"Error: Demo directory not found at {demo_dir}")
        return

    await init_db()

    seeded = {}

    demo_files = [
        ("demo_grounding.tif", demo_dir / "grounding" / "image.tif", "optical"),
        ("demo_t1.tif", demo_dir / "temporal" / "t1.tif", "optical"),
        ("demo_t2.tif", demo_dir / "temporal" / "t2.tif", "optical"),
        ("demo_optical.tif", demo_dir / "optical_sar" / "optical.tif", "optical"),
        ("demo_sar.tif", demo_dir / "optical_sar" / "sar.tif", "sar"),
    ]

    async with async_session_factory() as session:
        for alias, file_path, modality in demo_files:
            if not file_path.exists():
                print(f"Warning: Demo file missing at {file_path}")
                continue

            with open(file_path, "rb") as f:
                data = f.read()

            upload_res = await ImageService.upload_and_process(
                file_bytes=data,
                original_filename=alias,
                db=session
            )
            seeded[alias] = upload_res.id
            print(f"  Ingested {alias} -> Image ID: {upload_res.id}")

        await session.commit()

        # Seed BiTemporalPair for Demo 3
        if "demo_t1.tif" in seeded and "demo_t2.tif" in seeded:
            temporal_svc = get_temporal_service()
            t_pair = await temporal_svc.create_pair(
                BiTemporalPairCreate(
                    image_t1_id=seeded["demo_t1.tif"],
                    image_t2_id=seeded["demo_t2.tif"]
                ),
                db=session
            )
            print(f"  Created BiTemporalPair for Demo 3 -> Pair ID: {t_pair.pair_id} (valid={t_pair.validation.valid})")

        # Seed OpticalSARPair for Demo 4
        if "demo_optical.tif" in seeded and "demo_sar.tif" in seeded:
            cross_modal_svc = get_cross_modal_service()
            cm_pair = await cross_modal_svc.create_pair(
                OpticalSARPairCreate(
                    optical_image_id=seeded["demo_optical.tif"],
                    sar_image_id=seeded["demo_sar.tif"]
                ),
                db=session
            )
            print(f"  Created OpticalSARPair for Demo 4 -> Pair ID: {cm_pair.id} (valid={cm_pair.validation.valid})")

        await session.commit()

    print("=" * 60)
    print("Demo Assets Ingestion & Registration Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_demo_assets())
