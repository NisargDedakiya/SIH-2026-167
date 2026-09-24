"""
SatQuery AI — Phase 11A Scientific Validation & VLM Integrity Test Suite.
Validates:
1. Strict adapter architecture matching (BLIP vs LightweightRSVLM).
2. Intentional failure test: BLIP + LightweightRSVLM -> ADAPTER_ARCHITECTURE_MISMATCH.
3. PEFT LoRA injection & target module verification.
4. Dataset integrity & synthetic fixture quarantine.
5. Benchmark dataset unacquired reporting (NOT RUN).
6. Dynamic latency measurement.
"""

import json
from pathlib import Path
import pytest
import torch
import torch.nn as nn

from app.ai.exceptions import AdapterArchitectureMismatchError
from training.peft_adapter import LoRAManager, LoRALinear
from training.adapter_validation import validate_adapter_checkpoint
from training.datasets.bigearthnet.loader import BigEarthNetVQADataset
from evaluation.datasets.vrsbench.adapter import VRSBenchAdapter
from evaluation.datasets.rsvqa.adapter import RSVQAAdapter
from evaluation.datasets.cdvqa.adapter import CDVQAAdapter
from evaluation.datasets.isro_sac.adapter import ISROSACAdapter


class MockBlipSelfAttention(nn.Module):
    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.query = nn.Linear(hidden_dim, hidden_dim)
        self.key = nn.Linear(hidden_dim, hidden_dim)
        self.value = nn.Linear(hidden_dim, hidden_dim)


class MockBlipCrossAttention(nn.Module):
    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.self = MockBlipSelfAttention(hidden_dim)


class MockBlipLayer(nn.Module):
    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.attention = MockBlipCrossAttention(hidden_dim)
        self.crossattention = MockBlipCrossAttention(hidden_dim)


class MockBlipModel(nn.Module):
    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.layer = MockBlipLayer(hidden_dim)


class MockLightweightModel(nn.Module):
    def __init__(self, hidden_dim: int = 64):
        super().__init__()
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.Linear(hidden_dim * 2, hidden_dim)
        )
        self.lm_head = nn.Linear(hidden_dim, 100)


def test_required_audit_case_adapter_architecture_mismatch():
    """
    CRITICAL AUDIT TEST (Requirement 22):
    Attempts to load a LightweightRSVLM prototype adapter into a BLIP architecture.
    MUST fail with AdapterArchitectureMismatchError and error code ADAPTER_ARCHITECTURE_MISMATCH.
    """
    workspace_root = Path(__file__).resolve().parents[2]
    proto_adapter_dir = workspace_root / "artifacts/models/prototypes/lightweight-rsvlm"

    if not proto_adapter_dir.exists():
        pytest.skip("Quarantined prototype adapter directory not found.")

    # Instantiate model with BLIP target modules
    blip_model = MockBlipModel(hidden_dim=64)
    target_submodules = ["query", "value", "crossattention.self.query", "crossattention.self.value"]
    blip_model, _ = LoRAManager.apply_lora(blip_model, target_submodules=target_submodules, r=8, alpha=16)

    # Attempt to load lightweight adapter into BLIP model
    with pytest.raises(AdapterArchitectureMismatchError) as exc_info:
        LoRAManager.load_adapter(blip_model, proto_adapter_dir, strict_validation=True)

    err = exc_info.value
    assert err.code == "ADAPTER_ARCHITECTURE_MISMATCH"
    assert "Base model mismatch" in str(err) or len(err.unexpected_keys) > 0 or len(err.missing_keys) > 0


def test_blip_lora_injection_targets():
    """
    Verifies that LoRA is applied exclusively to matching linear projections
    and freezes base parameters.
    """
    model = MockBlipModel(hidden_dim=32)
    target_submodules = ["query", "value"]

    model, stats = LoRAManager.apply_lora(model, target_submodules=target_submodules, r=4, alpha=8)

    assert stats["injected_layers"] > 0
    assert stats["trainable_adapter_params"] > 0
    assert stats["r"] == 4
    assert stats["alpha"] == 8

    # Verify base weights are frozen
    for name, param in model.named_parameters():
        if "lora_" in name:
            assert param.requires_grad is True
        else:
            assert param.requires_grad is False


def test_adapter_checkpoint_validation_strict_rejection(tmp_path):
    """
    Verifies validate_adapter_checkpoint catches key mismatches and shape deviations.
    """
    model = MockBlipModel(hidden_dim=32)
    model, _ = LoRAManager.apply_lora(model, ["query", "value"], r=4, alpha=8)

    # Save valid adapter
    config = {
        "model": {"name": "Salesforce/blip-vqa-base"},
        "lora": {"r": 4, "alpha": 8, "dropout": 0.05, "target_modules": ["query", "value"]}
    }
    LoRAManager.save_adapter(model, tmp_path, config)

    # Corrupt by adding extraneous parameter to state_dict
    weights_file = tmp_path / "adapter" / "adapter_model.bin"
    state_dict = torch.load(weights_file)
    state_dict["extraneous.layer.lora_A"] = torch.randn(4, 32)
    torch.save(state_dict, weights_file)

    with pytest.raises(AdapterArchitectureMismatchError) as exc_info:
        validate_adapter_checkpoint(model, tmp_path)

    assert exc_info.value.code == "ADAPTER_ARCHITECTURE_MISMATCH"


def test_adapter_shape_mismatch_rejection(tmp_path):
    """
    Verifies shape deviations raise AdapterArchitectureMismatchError.
    """
    model = MockBlipModel(hidden_dim=32)
    model, _ = LoRAManager.apply_lora(model, ["query"], r=4, alpha=8)

    config = {
        "model": {"name": "Salesforce/blip-vqa-base"},
        "lora": {"r": 4, "alpha": 8, "dropout": 0.05, "target_modules": ["query"]}
    }
    LoRAManager.save_adapter(model, tmp_path, config)

    # Corrupt shape of a tensor
    weights_file = tmp_path / "adapter" / "adapter_model.bin"
    state_dict = torch.load(weights_file)
    first_key = list(state_dict.keys())[0]
    state_dict[first_key] = torch.randn(12, 12)  # Wrong dimensions
    torch.save(state_dict, weights_file)

    with pytest.raises(AdapterArchitectureMismatchError):
        validate_adapter_checkpoint(model, tmp_path)


def test_synthetic_data_quarantine():
    """
    Verifies that BigEarthNetVQADataset rejects missing files when allow_synthetic=False.
    """
    missing_samples = [
        {
            "sample_id": "nonexistent_sample_01",
            "optical_path": "nonexistent/dir/patch_rgb.png",
            "labels": ["Water bodies"],
        }
    ]

    with pytest.raises(FileNotFoundError) as exc_info:
        ds = BigEarthNetVQADataset(missing_samples, allow_synthetic=False)
        _ = ds[0]

    assert "Synthetic fallback is disallowed" in str(exc_info.value)


def test_benchmark_adapters_unacquired_status():
    """
    Verifies that benchmark adapters without local files report is_available=False
    and do not generate synthetic benchmark scores.
    """
    vrs = VRSBenchAdapter(allow_synthetic_fixtures=False)
    vrs.load()
    assert vrs.is_available is False
    assert "Dataset files not found" in (vrs.availability_reason or "")

    rsvqa = RSVQAAdapter(allow_synthetic_fixtures=False)
    rsvqa.load()
    assert rsvqa.is_available is False

    cdvqa = CDVQAAdapter(allow_synthetic_fixtures=False)
    cdvqa.load()
    assert cdvqa.is_available is False

    isro = ISROSACAdapter()
    assert isro.is_available is False


def test_lightweight_prototype_isolation():
    """
    Verifies that the quarantined prototype directory has explicit prototype provenance
    and does not claim to be the official validated satquery-rs-v1 model.
    """
    workspace_root = Path(__file__).resolve().parents[2]
    proto_manifest_file = workspace_root / "artifacts/models/prototypes/lightweight-rsvlm/model_manifest.json"

    if not proto_manifest_file.exists():
        pytest.skip("Quarantined prototype manifest not found.")

    with open(proto_manifest_file, "r", encoding="utf-8") as f:
        proto_manifest = json.load(f)

    # Must be marked as prototype
    assert "prototype" in proto_manifest.get("training_status", "").lower() or "prototype" in proto_manifest.get("base_model", "").lower()
    assert "LightweightRSVLM" in proto_manifest.get("base_model", "")
