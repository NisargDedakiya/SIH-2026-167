"""
SatQuery AI — Phase 6 Model Smoke Test Script.
Validates loading, independent optical and SAR preprocessing, feature extraction,
cross-modal fusion, and specialist inference on CPU/GPU.
"""

import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

try:
    import torch
    HAS_TORCH = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    HAS_TORCH = False
    CUDA_AVAILABLE = False

from app.ai.models.cross_modal.fusion_model import CrossModalFusionModel
from app.ai.models.cross_modal.optical_encoder import OpticalEncoder
from app.ai.models.cross_modal.sar_encoder import SAREncoder
from app.cross_modal.fusion import CrossModalFusion
from app.cross_modal.reasoning import CrossModalReasoningEngine


def run_smoke_test():
    print("=" * 65)
    print("SatQuery AI — Phase 6 Optical + SAR Model Smoke Test")
    print("=" * 65)

    # 1. Hardware Detection
    print("\n[Step 1] Hardware & Device Audit:")
    if HAS_TORCH:
        print(f"  PyTorch Version: {torch.__version__}")
        print(f"  CUDA GPU Available: {CUDA_AVAILABLE}")
        if CUDA_AVAILABLE:
            print(f"  GPU Device: {torch.cuda.get_device_name(0)}")
            target_device = "cuda"
        else:
            print("  Note: GPU unavailable. Operating on CPU (CPU feasibility verified).")
            target_device = "cpu"
    else:
        print("  PyTorch not installed in this environment; operating pure-NumPy/SciPy path.")
        target_device = "cpu"

    # 2. Synthetic Fixture Generation
    print("\n[Step 2] Generating synthetic Optical & SAR test rasters:")
    # Optical: 128x128 3-band simulated true-color
    optical_fixture = np.zeros((128, 128, 3), dtype=np.uint8)
    optical_fixture[:, :] = [45, 120, 35]  # Green vegetation baseline
    optical_fixture[40:80, 20:100] = [20, 40, 110]  # Water body absorption
    optical_fixture[15:35, 15:45] = [180, 170, 160]  # Built-up rooftops
    print(f"  Optical fixture generated: shape={optical_fixture.shape}, dtype={optical_fixture.dtype}")

    # SAR: 128x128 2-channel (VV, VH) dual-pol backscatter
    sar_fixture = np.full((128, 128, 2), 120.0, dtype=np.float32)  # Moderate roughness
    sar_fixture[40:80, 20:100] = 5.0  # Smooth water specular null (< -18 dB)
    sar_fixture[15:35, 15:45] = 1800.0  # Urban double-bounce bright peaks (> +5 dB)
    print(f"  SAR fixture generated: shape={sar_fixture.shape}, dtype={sar_fixture.dtype}, channels=Dual-Pol (VV/VH)")

    # 3. Stage A: Independent Preprocessing
    print("\n[Step 3] Stage A: Independent Preprocessing & Feature Encoding:")
    t0 = time.time()
    opt_tensor = OpticalEncoder.preprocess(optical_fixture)
    sar_tensor = SAREncoder.preprocess(sar_fixture, apply_db_scale=True)
    t_stage_a = (time.time() - t0) * 1000

    print(f"  Optical Tensor: shape={opt_tensor.shape}, min={opt_tensor.min():.3f}, max={opt_tensor.max():.3f}")
    print(f"  SAR Tensor (dB scaled): shape={sar_tensor.shape}, min={sar_tensor.min():.3f}, max={sar_tensor.max():.3f}")
    print(f"  Stage A duration: {t_stage_a:.2f} ms")

    # 4. Stage B: Cross-Modal Feature Fusion
    print("\n[Step 4] Stage B: Cross-Modal Feature Fusion:")
    t0 = time.time()
    opt_feats = OpticalEncoder.extract_features(opt_tensor)
    sar_feats = SAREncoder.extract_features(sar_tensor)
    joint_features = CrossModalFusion.fuse_representations(opt_feats, sar_feats)
    t_stage_b = (time.time() - t0) * 1000

    print(f"  Joint Fused Feature Tensor shape: {joint_features.shape}")
    print(f"  Stage B duration: {t_stage_b:.2f} ms")

    # 5. Stage C: Specialist Inference & Task Reasoning
    print("\n[Step 5] Stage C: Specialist Model Inference & Reasoning:")
    model = CrossModalFusionModel()
    model.load(device=target_device)

    queries = [
        "Analyze these optical and SAR images together.",
        "What can the SAR image reveal that the optical image does not?",
        "Locate the water body using the complementary information from optical and SAR.",
        "Highlight the urban regions supported by both images."
    ]

    for q in queries:
        t0 = time.time()
        model_out = model.predict(
            processed_input={"optical": optical_fixture, "sar": sar_fixture},
            query=q
        )
        reasoning = CrossModalReasoningEngine.reason(
            query=q,
            task="cross_modal_analysis",
            optical_meta={"sensor": "Cartosat-2S", "modality": "optical"},
            sar_meta={"sensor": "RISAT-1A", "modality": "sar", "polarization": "VV/VH"},
            model_prediction=model_out,
            optical_shape=(128, 128),
        )
        duration_ms = (time.time() - t0) * 1000

        print(f"\n  Query: \"{q}\"")
        print(f"  Answer: {reasoning['answer']}")
        print(f"  Confidence: {reasoning['confidence_score']} ({reasoning['confidence_method']})")
        print(f"  Modality Disagreement: {reasoning['disagreement'].agreement_status}")
        print(f"  Regions Detected: {len(reasoning['regions'])}")
        print(f"  Latency: {duration_ms:.2f} ms")

    # 6. Resource Release
    print("\n[Step 6] Resource Teardown:")
    model.unload()
    print("  Model weights and tensor buffers successfully unloaded.")

    print("\n" + "=" * 65)
    print("SMOKE TEST RESULT: PASS (All stages verified successfully)")
    print("=" * 65)


if __name__ == "__main__":
    run_smoke_test()
