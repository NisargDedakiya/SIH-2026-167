"""
SatQuery AI — Real Model Smoke Test Script.

Validates end-to-end execution of real PyTorch/Transformers remote-sensing
specialist models (VQA and Scene Captioning) on an actual or synthetic GeoTIFF.

Usage:
    python scripts/test_real_models.py [--device cpu|cuda]
"""

import argparse
import io
import sys
import time
from pathlib import Path
import numpy as np

# Ensure backend app is in python path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.ai.models.caption.rs_caption_adapter import RsCaptionModel
from app.ai.models.vqa.rs_vqa_adapter import RsVqaModel
from app.ai.preprocessing import RemoteSensingPreprocessor


def generate_sample_geotiff() -> bytes:
    import rasterio
    from rasterio.transform import from_origin

    buf = io.BytesIO()
    data = (np.random.rand(3, 256, 256) * 3000).astype(np.uint16)
    transform = from_origin(500000, 3000000, 10, 10)

    with rasterio.open(
        buf,
        "w",
        driver="GTiff",
        height=256,
        width=256,
        count=3,
        dtype="uint16",
        crs="EPSG:32643",
        transform=transform,
    ) as dst:
        dst.write(data)

    return buf.getvalue()


def run_smoke_test(device: str = "cpu"):
    print("=" * 65)
    print(f" SatQuery AI — Remote-Sensing Specialist Model Smoke Test")
    print(f" Target Device: {device.upper()}")
    print("=" * 65)

    try:
        import torch
        import transformers
        print(f"[✓] PyTorch version: {torch.__version__}")
        print(f"[✓] Transformers version: {transformers.__version__}")
        print(f"[✓] CUDA Available: {torch.cuda.is_available()}")
    except ImportError as e:
        print(f"[!] Error: PyTorch or Transformers is not installed ({e}).")
        print("    Install them using: pip install torch torchvision transformers")
        sys.exit(1)

    # 1. Prepare Satellite Raster
    print("\n[1/3] Generating synthetic multispectral GeoTIFF (3 bands, uint16)...")
    raster_bytes = generate_sample_geotiff()
    metadata = {"modality": "optical", "nodata": None}
    print("      Raster generated successfully (size:", len(raster_bytes), "bytes).")

    # 2. Test Remote-Sensing VQA Model
    print("\n[2/3] Initializing and testing Remote-Sensing VQA Specialist Model...")
    vqa_model = RsVqaModel()
    print(f"      Model ID: {vqa_model.model_id}")
    t0 = time.time()
    vqa_model.load(device=device)
    load_time = time.time() - t0
    print(f"      Model loaded in {load_time:.2f}s.")

    query = "What type of land cover is visible in this satellite image?"
    print(f"      Executing query: '{query}'")
    t1 = time.time()
    vqa_result = vqa_model.run(
        image_bytes=raster_bytes,
        metadata=metadata,
        query=query
    )
    vqa_time = time.time() - t1

    print(f"      [✓] Answer: {vqa_result['result']['answer']}")
    print(f"      [✓] Confidence: {vqa_result['confidence']['score'] * 100:.1f}% ({vqa_result['confidence']['method']})")
    print(f"      [✓] Inference time: {vqa_time:.2f}s")

    # 3. Test Remote-Sensing Captioning Model
    print("\n[3/3] Initializing and testing Remote-Sensing Captioning Specialist Model...")
    caption_model = RsCaptionModel()
    print(f"      Model ID: {caption_model.model_id}")
    t2 = time.time()
    caption_model.load(device=device)
    cap_load_time = time.time() - t2
    print(f"      Model loaded in {cap_load_time:.2f}s.")

    t3 = time.time()
    cap_result = caption_model.run(
        image_bytes=raster_bytes,
        metadata=metadata
    )
    cap_time = time.time() - t3

    print(f"      [✓] Scene Caption: {cap_result['result']['caption']}")
    print(f"      [✓] Confidence: {cap_result['confidence']['score'] * 100:.1f}% ({cap_result['confidence']['method']})")
    print(f"      [✓] Inference time: {cap_time:.2f}s")

    print("\n" + "=" * 65)
    print(" ALL REAL MODEL ADAPTERS PASSED SMOKE TEST SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test real AI models")
    parser.add_argument("--device", choices=["cpu", "cuda", "auto"], default="auto")
    args = parser.parse_args()

    dev = args.device
    if dev == "auto":
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"

    run_smoke_test(device=dev)
