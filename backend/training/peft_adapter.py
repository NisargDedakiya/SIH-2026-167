"""
Self-Contained Parameter-Efficient Fine-Tuning (PEFT / LoRA) Engine.
Implements Low-Rank Adaptation (Hu et al.) for Vision-Language Models without external dependencies.
W = W_0 + (alpha / r) * (B @ A)
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import torch
import torch.nn as nn


class LoRALinear(nn.Module):
    """
    Low-Rank Adaptation wrapper for PyTorch Linear layers.
    W = W_0 + (alpha / r) * (B @ A)
    """

    def __init__(
        self,
        base_layer: nn.Linear,
        r: int = 8,
        alpha: int = 16,
        dropout: float = 0.05,
    ):
        super().__init__()
        self.base_layer = base_layer
        self.r = r
        self.alpha = alpha
        self.scaling = alpha / r

        # Freeze base parameters
        for param in self.base_layer.parameters():
            param.requires_grad = False

        in_features = base_layer.in_features
        out_features = base_layer.out_features

        # LoRA projection matrices: A (r x in), B (out x r)
        self.lora_A = nn.Parameter(torch.empty(r, in_features))
        self.lora_B = nn.Parameter(torch.empty(out_features, r))

        if dropout > 0.0:
            self.lora_dropout = nn.Dropout(p=dropout)
        else:
            self.lora_dropout = nn.Identity()

        self.reset_parameters()

    def reset_parameters(self) -> None:
        # Initialize A with Kaiming uniform, B with zeros (so initial Delta W is 0)
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    @property
    def weight(self):
        return self.base_layer.weight

    @property
    def bias(self):
        return self.base_layer.bias

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.base_layer(x)
        lora_out = (self.lora_dropout(x) @ self.lora_A.T) @ self.lora_B.T
        return base_out + lora_out * self.scaling


class LoRAManager:
    """
    Applies, manages, saves, and loads LoRA adapters on PyTorch models.
    """

    @classmethod
    def apply_lora(
        cls,
        model: nn.Module,
        target_submodules: Optional[List[str]] = None,
        r: int = 8,
        alpha: int = 16,
        dropout: float = 0.05,
    ) -> Tuple[nn.Module, Dict[str, Any]]:
        """
        Injects LoRALinear layers into target linear projections and freezes all base parameters.
        """
        target_keys = target_submodules or ["query", "value", "crossattention", "classifier", "dense"]

        # Freeze all base model parameters first
        for param in model.parameters():
            param.requires_grad = False

        injected_count = 0
        total_lora_params = 0

        # Collect layers to replace first (avoid mutating during iteration)
        replacements = []
        for name, module in list(model.named_modules()):
            for child_name, child_module in list(module.named_children()):
                if isinstance(child_module, nn.Linear) and not isinstance(child_module, LoRALinear):
                    full_name = f"{name}.{child_name}" if name else child_name
                    matches = any(target in full_name for target in target_keys)
                    if matches:
                        replacements.append((module, child_name, child_module))

        for module, child_name, child_module in replacements:
            lora_wrapper = LoRALinear(
                base_layer=child_module,
                r=r,
                alpha=alpha,
                dropout=dropout
            )
            setattr(module, child_name, lora_wrapper)
            injected_count += 1
            total_lora_params += (lora_wrapper.lora_A.numel() + lora_wrapper.lora_B.numel())

        stats = {
            "injected_layers": injected_count,
            "trainable_adapter_params": total_lora_params,
            "r": r,
            "alpha": alpha,
            "dropout": dropout,
            "target_keys": target_keys
        }
        return model, stats

    @classmethod
    def extract_adapter_state_dict(cls, model: nn.Module) -> Dict[str, torch.Tensor]:
        """
        Extracts only trainable LoRA parameter tensors (A and B matrices).
        """
        adapter_state: Dict[str, torch.Tensor] = {}
        for name, param in model.named_parameters():
            if "lora_A" in name or "lora_B" in name:
                adapter_state[name] = param.detach().cpu()
        return adapter_state

    @classmethod
    def save_adapter(
        cls,
        model: nn.Module,
        output_dir: str | Path,
        config: Dict[str, Any]
    ) -> Path:
        """
        Saves adapter weights and configuration files.
        """
        out_path = Path(output_dir)
        adapter_dir = out_path / "adapter"
        adapter_dir.mkdir(parents=True, exist_ok=True)

        adapter_weights = cls.extract_adapter_state_dict(model)
        torch.save(adapter_weights, adapter_dir / "adapter_model.bin")

        adapter_config = {
            "peft_type": "LORA",
            "r": config.get("lora", {}).get("r", 8),
            "lora_alpha": config.get("lora", {}).get("alpha", 16),
            "lora_dropout": config.get("lora", {}).get("dropout", 0.05),
            "target_modules": config.get("lora", {}).get("target_modules", []),
            "base_model_name_or_path": config.get("model", {}).get("name", "Salesforce/blip-vqa-base"),
            "num_adapter_parameters": sum(p.numel() for p in adapter_weights.values()),
        }

        with open(adapter_dir / "adapter_config.json", "w", encoding="utf-8") as f:
            json.dump(adapter_config, f, indent=2)

        return adapter_dir

    @classmethod
    def load_adapter(
        cls,
        model: nn.Module,
        adapter_dir: str | Path
    ) -> nn.Module:
        """
        Loads saved LoRA weights into an existing model that has LoRA layers injected.
        """
        adapter_path = Path(adapter_dir)
        weights_file = adapter_path / "adapter_model.bin"
        if not weights_file.exists():
            weights_file = adapter_path / "adapter" / "adapter_model.bin"

        if not weights_file.exists():
            raise FileNotFoundError(f"Adapter weights file not found in {adapter_dir}")

        state_dict = torch.load(weights_file, map_location="cpu")
        model.load_state_dict(state_dict, strict=False)
        return model
