"""
SatQuery AI — LoRA Adapter Architecture Validation Engine (Phase 11A).
Guarantees strict architectural alignment between base foundation VLM backbones
and fine-tuned LoRA checkpoints, preventing silent strict=False loading bugs.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import torch
import torch.nn as nn

from app.ai.exceptions import AdapterArchitectureMismatchError


def validate_adapter_checkpoint(
    model: nn.Module,
    adapter_dir: str | Path,
    expected_base_model: Optional[str] = None,
    expected_target_modules: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validates a saved LoRA adapter checkpoint against an active PyTorch model.
    Throws AdapterArchitectureMismatchError if any incompatibility, missing key,
    or unexpected parameter is detected.

    Returns a summary dictionary of validated parameters and tensor shapes.
    """
    path = Path(adapter_dir)
    weights_file = path / "adapter_model.bin"
    if not weights_file.exists():
        weights_file = path / "adapter" / "adapter_model.bin"
    if not weights_file.exists():
        raise FileNotFoundError(f"LoRA adapter weights file not found in '{adapter_dir}'")

    config_file = path / "adapter_config.json"
    if not config_file.exists():
        config_file = path / "adapter" / "adapter_config.json"
    if not config_file.exists():
        raise FileNotFoundError(f"LoRA adapter config not found in '{adapter_dir}'")

    with open(config_file, "r", encoding="utf-8") as f:
        adapter_config = json.load(f)

    # 1. Base model identity check
    ckpt_base = adapter_config.get("base_model_name_or_path") or adapter_config.get("base_model", "")
    if expected_base_model and ckpt_base:
        # Normalize comparison (e.g. ignore casing or prefix)
        if expected_base_model.lower() not in ckpt_base.lower() and ckpt_base.lower() not in expected_base_model.lower():
            raise AdapterArchitectureMismatchError(
                f"Base model mismatch: checkpoint was built for '{ckpt_base}' "
                f"but runtime expected '{expected_base_model}'.",
                unexpected_keys=[ckpt_base]
            )

    # 2. Target modules check
    if expected_target_modules:
        ckpt_targets = adapter_config.get("target_modules", [])
        if ckpt_targets:
            # Check overlap or matching targets
            mismatched = set(ckpt_targets).symmetric_difference(set(expected_target_modules))
            # If completely disjoint, raise error
            if not set(ckpt_targets).intersection(set(expected_target_modules)):
                raise AdapterArchitectureMismatchError(
                    f"Target modules mismatch between checkpoint ({ckpt_targets}) "
                    f"and model ({expected_target_modules}).",
                    unexpected_keys=list(mismatched)
                )

    # 3. Load state dict and inspect keys against model's active LoRA parameters
    state_dict = torch.load(weights_file, map_location="cpu")
    model_lora_params = {
        name: param for name, param in model.named_parameters()
        if "lora_A" in name or "lora_B" in name
    }

    if not model_lora_params:
        raise AdapterArchitectureMismatchError(
            "Target model has no injected LoRA layers (zero lora_A / lora_B parameters found). "
            "Ensure LoRAManager.apply_lora() has been executed prior to loading adapter."
        )

    ckpt_keys = set(state_dict.keys())
    model_keys = set(model_lora_params.keys())

    missing_keys = list(model_keys - ckpt_keys)
    unexpected_keys = list(ckpt_keys - model_keys)

    if unexpected_keys or missing_keys:
        err_msg = (
            f"ADAPTER_ARCHITECTURE_MISMATCH: Checkpoint tensor keys do not match model LoRA layers. "
            f"Missing keys: {len(missing_keys)}, Unexpected keys: {len(unexpected_keys)}."
        )
        raise AdapterArchitectureMismatchError(
            err_msg,
            missing_keys=missing_keys,
            unexpected_keys=unexpected_keys
        )

    # 4. Shape verification
    for key in model_keys:
        ckpt_shape = list(state_dict[key].shape)
        model_shape = list(model_lora_params[key].shape)
        if ckpt_shape != model_shape:
            raise AdapterArchitectureMismatchError(
                f"Tensor shape mismatch for parameter '{key}': "
                f"checkpoint has {ckpt_shape}, but model expected {model_shape}.",
                unexpected_keys=[f"{key}:{ckpt_shape}"]
            )

    total_params = sum(p.numel() for p in state_dict.values())
    return {
        "status": "VALIDATED",
        "base_model": ckpt_base,
        "adapter_parameters": total_params,
        "matched_keys": len(model_keys),
        "r": adapter_config.get("r"),
        "alpha": adapter_config.get("lora_alpha"),
    }
