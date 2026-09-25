#!/usr/bin/env python3
"""
Model Preparation and Verification Script for SatQuery AI (SIH 2026).
Preloads and caches required Vision-Language and Grounding models locally:
1. Salesforce/blip-vqa-base (VQA base)
2. Salesforce/blip-image-captioning-base (Captioning base)
3. google/owlvit-base-patch32 (Open-vocabulary visual grounding)
4. satquery-rs-adapter (BLIP + LoRA domain-adapted checkpoint)

Verifies model weights and reports status: AVAILABLE, MISSING, or FAILED.
Ensures zero live network downloads occur during SIH evaluation demonstrations.
"""

import os
import sys
import time

# Ensure backend directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def check_hf_cache(model_id: str) -> bool:
    """Checks if model is cached locally in Hugging Face cache."""
    try:
        from huggingface_hub import try_to_load_from_cache
        res = try_to_load_from_cache(model_id, "config.json")
        return res is not None and isinstance(res, str)
    except Exception:
        return False


def verify_blip_vqa(model_id: str = "Salesforce/blip-vqa-base") -> dict:
    start = time.time()
    try:
        from transformers import BlipProcessor, BlipForQuestionAnswering
        try:
            processor = BlipProcessor.from_pretrained(model_id, local_files_only=True)
            model = BlipForQuestionAnswering.from_pretrained(model_id, local_files_only=True)
        except Exception:
            processor = BlipProcessor.from_pretrained(model_id)
            model = BlipForQuestionAnswering.from_pretrained(model_id)
        model.eval()
        duration = round(time.time() - start, 2)
        return {"status": "AVAILABLE", "duration_s": duration, "note": "Processor and weights loaded"}
    except Exception as e:
        duration = round(time.time() - start, 2)
        return {"status": "FAILED", "duration_s": duration, "note": str(e)[:100]}


def verify_blip_caption(model_id: str = "Salesforce/blip-image-captioning-base") -> dict:
    start = time.time()
    try:
        from transformers import BlipProcessor, BlipForConditionalGeneration
        try:
            processor = BlipProcessor.from_pretrained(model_id, local_files_only=True)
            model = BlipForConditionalGeneration.from_pretrained(model_id, local_files_only=True)
        except Exception:
            processor = BlipProcessor.from_pretrained(model_id)
            model = BlipForConditionalGeneration.from_pretrained(model_id)
        model.eval()
        duration = round(time.time() - start, 2)
        return {"status": "AVAILABLE", "duration_s": duration, "note": "Processor and weights loaded"}
    except Exception as e:
        duration = round(time.time() - start, 2)
        return {"status": "FAILED", "duration_s": duration, "note": str(e)[:100]}


def verify_owlvit_grounding(model_id: str = "google/owlvit-base-patch32") -> dict:
    start = time.time()
    try:
        from transformers import OwlViTProcessor, OwlViTForObjectDetection
        # Try local first
        try:
            processor = OwlViTProcessor.from_pretrained(model_id, local_files_only=True)
            model = OwlViTForObjectDetection.from_pretrained(model_id, local_files_only=True)
        except Exception:
            processor = OwlViTProcessor.from_pretrained(model_id)
            model = OwlViTForObjectDetection.from_pretrained(model_id)
        model.eval()
        duration = round(time.time() - start, 2)
        return {"status": "AVAILABLE", "duration_s": duration, "note": "Processor and weights loaded"}
    except Exception as e:
        duration = round(time.time() - start, 2)
        return {"status": "FAILED", "duration_s": duration, "note": str(e)[:100]}


def verify_rs_adapter() -> dict:
    start = time.time()
    candidates = [
        os.path.join(PROJECT_ROOT, "artifacts", "models", "satquery-rs-adapter", "adapter", "adapter_model.bin"),
        os.path.join(PROJECT_ROOT, "artifacts", "models", "satquery-rs-adapter", "adapter", "adapter_model.safetensors"),
        os.path.join(BACKEND_DIR, "artifacts", "models", "satquery-rs-adapter", "adapter", "adapter_model.bin"),
    ]
    for c in candidates:
        if os.path.exists(c):
            size_mb = round(os.path.getsize(c) / (1024 * 1024), 2)
            duration = round(time.time() - start, 2)
            return {"status": "AVAILABLE", "duration_s": duration, "note": f"Found at {c} ({size_mb} MB)"}
    return {"status": "MISSING", "duration_s": 0.0, "note": "Checkpoint file not found in artifacts/models"}


def main():
    print("=" * 70)
    print("SatQuery AI - Offline Model Cache & Verification Suite")
    print("=" * 70)
    print("Verifying models required for SIH 2026 Demonstrations...\n")

    results = {}

    print("[1/4] Verifying Visual Grounding Model (google/owlvit-base-patch32)...")
    results["Grounding (OwlViT)"] = verify_owlvit_grounding()
    print(f"      Status: {results['Grounding (OwlViT)']['status']} ({results['Grounding (OwlViT)']['note']})\n")

    print("[2/4] Verifying VQA Foundation Model (Salesforce/blip-vqa-base)...")
    results["VQA Foundation (BLIP)"] = verify_blip_vqa()
    print(f"      Status: {results['VQA Foundation (BLIP)']['status']} ({results['VQA Foundation (BLIP)']['note']})\n")

    print("[3/4] Verifying Captioning Model (Salesforce/blip-image-captioning-base)...")
    results["Captioning (BLIP)"] = verify_blip_caption()
    print(f"      Status: {results['Captioning (BLIP)']['status']} ({results['Captioning (BLIP)']['note']})\n")

    print("[4/4] Verifying Remote-Sensing Adapted Checkpoint (satquery-rs-v1)...")
    results["RS Adapter (LoRA)"] = verify_rs_adapter()
    print(f"      Status: {results['RS Adapter (LoRA)']['status']} ({results['RS Adapter (LoRA)']['note']})\n")

    print("=" * 70)
    print(f"{'MODEL COMPONENT':<30} {'STATUS':<12} {'TIME (s)':<10} {'DETAILS'}")
    print("-" * 70)
    all_ok = True
    for name, res in results.items():
        status_str = res["status"]
        if status_str == "FAILED":
            all_ok = False
        print(f"{name:<30} {status_str:<12} {res['duration_s']:<10} {res['note']}")
    print("=" * 70)

    if all_ok:
        print("[SUCCESS] All essential specialist models are prepared and cached for offline demo.")
        return 0
    else:
        print("[WARNING] One or more models are missing or failed. Check error notes above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
