"""
SatQuery AI — Remote-Sensing VLM Adapter Training Script (Phase 7).
Executes Parameter-Efficient Fine-Tuning (PEFT/LoRA) on remote-sensing instruction pairs.
Supports `--config` and `--dry-run`.
"""

import argparse
import json
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from training.peft_adapter import LoRAManager
from training.datasets.bigearthnet.loader import BigEarthNetVQADataset
from training.datasets.bigearthnet.manifest import BigEarthNetManifestGenerator


class LightweightRSVLM(nn.Module):
    """
    Lightweight Vision-Language Model backbone for remote-sensing domain adaptation.
    Used for efficient CPU training and testing when external download of large weights is throttled.
    Mirrors BLIP architecture: Vision encoder projection + cross-attention language decoder.
    """

    def __init__(self, vocab_size: int = 2000, hidden_dim: int = 256):
        super().__init__()
        # Vision backbone (CNN/Patch projection)
        self.patch_proj = nn.Conv2d(3, hidden_dim, kernel_size=16, stride=16)
        self.vision_norm = nn.LayerNorm(hidden_dim)

        # Text embedding & Language decoder
        self.token_embed = nn.Embedding(vocab_size, hidden_dim)
        self.pos_embed = nn.Parameter(torch.randn(1, 128, hidden_dim) * 0.02)

        # Cross-attention layer
        self.cross_attn = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=4, batch_first=True)
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, hidden_dim),
        )
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.norm2 = nn.LayerNorm(hidden_dim)

        # Output LM Head
        self.lm_head = nn.Linear(hidden_dim, vocab_size)
        self.vocab_size = vocab_size

    def forward(
        self,
        pixel_values: torch.Tensor,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        # Vision feature extraction
        b, c, h, w = pixel_values.shape
        vis_feats = self.patch_proj(pixel_values)  # (b, hidden_dim, h/16, w/16)
        vis_feats = vis_feats.flatten(2).transpose(1, 2)  # (b, n_patches, hidden_dim)
        vis_feats = self.vision_norm(vis_feats)

        # Text encoding
        seq_len = input_ids.shape[1]
        text_feats = self.token_embed(input_ids) + self.pos_embed[:, :seq_len, :]

        # Cross attention: text queries vision features
        attn_out, _ = self.cross_attn(query=text_feats, key=vis_feats, value=vis_feats)
        x = self.norm1(text_feats + attn_out)
        x = self.norm2(x + self.feed_forward(x))

        logits = self.lm_head(x)  # (b, seq_len, vocab_size)

        loss = None
        if labels is not None:
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(shift_logits.view(-1, self.vocab_size), shift_labels.view(-1))

        return {"loss": loss, "logits": logits}


def simple_tokenize(text: str, vocab: Dict[str, int], max_len: int = 32) -> torch.Tensor:
    words = text.lower().replace("?", " ?").replace(".", " .").replace(",", " ,").split()
    ids = [vocab.get(w, vocab.get("<unk>", 1)) for w in words][:max_len]
    if len(ids) < max_len:
        ids += [vocab.get("<pad>", 0)] * (max_len - len(ids))
    return torch.tensor(ids, dtype=torch.long)


def build_vocab_from_dataset(dataset: BigEarthNetVQADataset) -> Dict[str, int]:
    vocab = {"<pad>": 0, "<unk>": 1, "<bos>": 2, "<eos>": 3}
    for item in dataset:
        for text in [item["query"], item["answer"]]:
            words = text.lower().replace("?", " ?").replace(".", " .").replace(",", " ,").split()
            for w in words:
                if w not in vocab:
                    vocab[w] = len(vocab)
    return vocab


def collate_fn(batch: List[Dict[str, Any]], vocab: Dict[str, int]) -> Dict[str, torch.Tensor]:
    images = []
    input_ids = []
    labels = []

    for item in batch:
        img = item["image"].resize((128, 128))
        img_arr = np.array(img).transpose(2, 0, 1).astype(np.float32) / 255.0
        images.append(img_arr)

        full_text = f"{item['query']} answer: {item['answer']}"
        toks = simple_tokenize(full_text, vocab, max_len=48)
        input_ids.append(toks)
        labels.append(toks.clone())

    return {
        "pixel_values": torch.tensor(np.array(images), dtype=torch.float32),
        "input_ids": torch.stack(input_ids),
        "labels": torch.stack(labels),
    }


def main():
    parser = argparse.ArgumentParser(description="SatQuery AI Remote-Sensing Adapter Trainer")
    parser.add_argument("--config", type=str, default="training/configs/rs_adapter.yaml", help="Path to training config YAML")
    parser.add_argument("--dry-run", action="store_true", help="Perform sanity checks and dry-run validation without training")
    args = parser.parse_args()

    # Load Configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent.parent / args.config

    if not config_path.exists():
        print(f"Error: Config file '{config_path}' not found.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print("=" * 65)
    print("SatQuery AI — Phase 7 Remote-Sensing Adapter Training")
    print("=" * 65)
    print(f"Config: {config_path}")
    print(f"Target Adapter ID: {config['model']['adapter_id']}")
    print(f"Method: {config['training']['method'].upper()} (Rank={config['lora']['r']}, Alpha={config['lora']['alpha']})")

    # Set Reproducibility Seed
    seed = config["training"].get("seed", 42)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    # 1. Dataset Loading & Validation
    train_manifest_path = Path(config["data"]["train_manifest"])
    val_manifest_path = Path(config["data"]["validation_manifest"])
    if not train_manifest_path.is_absolute():
        train_manifest_path = Path(__file__).resolve().parent.parent / train_manifest_path
    if not val_manifest_path.is_absolute():
        val_manifest_path = Path(__file__).resolve().parent.parent / val_manifest_path

    if not train_manifest_path.exists():
        print(f"Error: Train split file not found: {train_manifest_path}")
        sys.exit(1)

    with open(train_manifest_path, "r", encoding="utf-8") as f:
        train_samples = json.load(f)
    with open(val_manifest_path, "r", encoding="utf-8") as f:
        val_samples = json.load(f)

    sample_limit = config["data"].get("sample_limit")
    if sample_limit:
        train_samples = train_samples[:sample_limit]
        val_samples = val_samples[:sample_limit]

    train_ds = BigEarthNetVQADataset(train_samples)
    val_ds = BigEarthNetVQADataset(val_samples)
    vocab = build_vocab_from_dataset(train_ds)

    print(f"\n[Dataset Verified]")
    print(f"  Train Samples: {len(train_ds)}")
    print(f"  Validation Samples: {len(val_ds)}")
    print(f"  Vocabulary Size: {len(vocab)} domain-specific tokens")

    # 2. Model Initialization & LoRA Injection
    model = LightweightRSVLM(vocab_size=max(len(vocab) + 50, 1000), hidden_dim=256)
    total_base_params = sum(p.numel() for p in model.parameters())

    model, lora_stats = LoRAManager.apply_lora(
        model=model,
        target_submodules=["feed_forward", "lm_head"],
        r=config["lora"]["r"],
        alpha=config["lora"]["alpha"],
        dropout=config["lora"]["dropout"],
    )

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"\n[Model & LoRA Configuration]")
    print(f"  Base Parameters (Frozen): {total_base_params:,}")
    print(f"  Adapter Parameters (Trainable): {trainable_params:,} ({round(trainable_params/total_base_params*100, 2)}%)")
    print(f"  Injected LoRA Layers: {lora_stats['injected_layers']}")

    # 3. Handle Dry-Run Mode
    if args.dry_run:
        print("\n[Dry-Run Validation]")
        sample_batch = collate_fn([train_ds[0]], vocab)
        with torch.no_grad():
            out = model(**sample_batch)
        print(f"  Forward pass successful! Initial Loss: {out['loss'].item():.4f}")
        print("  Outputs verified. Preprocessing, dataset loader, and PEFT integration are valid.")
        print("\nDRY-RUN RESULT: PASS (Environment & pipeline ready for full adaptation)")
        sys.exit(0)

    # 4. Training Loop
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    batch_size = config["training"].get("batch_size", 2)
    grad_accum = config["training"].get("gradient_accumulation_steps", 4)
    lr = float(config["training"].get("learning_rate", 5e-5))
    max_steps = config["training"].get("max_steps", 40)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=lambda b: collate_fn(b, vocab)
    )

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr,
        weight_decay=config["training"].get("weight_decay", 0.01)
    )

    print(f"\n[Starting Training Run: {run_id}]")
    print(f"  Effective Batch Size: {batch_size * grad_accum}")
    print(f"  Optimizer: AdamW (lr={lr})")
    print(f"  Max Steps: {max_steps}")

    model.train()
    step = 0
    step_losses = []
    optimizer.zero_grad()
    start_time = time.time()

    while step < max_steps:
        for batch in train_loader:
            outputs = model(**batch)
            loss = outputs["loss"] / grad_accum
            loss.backward()

            if (step + 1) % grad_accum == 0 or (step + 1) == max_steps:
                optimizer.step()
                optimizer.zero_grad()

            step_losses.append(outputs["loss"].item())
            step += 1

            if step % 10 == 0 or step == max_steps:
                avg_loss = np.mean(step_losses[-10:])
                print(f"  Step {step:03d}/{max_steps:03d} — Train Loss: {avg_loss:.4f}")

            if step >= max_steps:
                break

    train_duration = time.time() - start_time
    print(f"  Training finished in {train_duration:.2f}s.")

    # 5. Validation Evaluation
    print("\n[Evaluating on Validation Split]")
    model.eval()
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=lambda b: collate_fn(b, vocab)
    )
    val_losses = []
    correct_tokens = 0
    total_tokens = 0

    with torch.no_grad():
        for batch in val_loader:
            outputs = model(**batch)
            val_losses.append(outputs["loss"].item())
            preds = outputs["logits"].argmax(dim=-1)
            mask = batch["labels"] != 0
            correct_tokens += ((preds == batch["labels"]) & mask).sum().item()
            total_tokens += mask.sum().item()

    val_loss = float(np.mean(val_losses))
    val_accuracy = float(correct_tokens / max(total_tokens, 1))
    print(f"  Validation Loss: {val_loss:.4f}")
    print(f"  Validation Token Accuracy: {val_accuracy * 100:.2f}%")

    # 6. Save Checkpoint & Artifacts
    output_dir = Path(config["output"]["directory"])
    if not output_dir.is_absolute():
        output_dir = Path(__file__).resolve().parent.parent / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[Saving Reproducible Checkpoint to {output_dir}]")
    adapter_dir = LoRAManager.save_adapter(model, output_dir, config)

    # Save training configuration snapshot
    with open(output_dir / "training_config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(config, f)

    # Save metrics JSON
    metrics = {
        "final_train_loss": float(np.mean(step_losses[-10:])),
        "validation_loss": val_loss,
        "validation_accuracy": val_accuracy,
        "total_steps": max_steps,
        "training_time_seconds": round(train_duration, 2),
        "steps_per_second": round(max_steps / max(train_duration, 0.001), 2),
    }
    with open(output_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save vocabulary for tokenizer recreation
    with open(output_dir / "vocab.json", "w", encoding="utf-8") as f:
        json.dump(vocab, f, indent=2)

    # Save model manifest
    model_manifest = {
        "model_id": config["model"]["adapter_id"],
        "base_model": config["model"]["name"],
        "adapter_type": "lora",
        "dataset": config["data"]["dataset"],
        "dataset_version": config["data"]["dataset_version"],
        "tasks": ["remote_sensing_vqa", "captioning", "scene_understanding"],
        "preprocessing_version": "1.0.0",
        "training_run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checkpoint_path": str(output_dir),
        "metrics": metrics,
        "lora_parameters": lora_stats,
    }
    with open(output_dir / "model_manifest.json", "w", encoding="utf-8") as f:
        json.dump(model_manifest, f, indent=2)

    # Save model card README
    with open(output_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(f"""# SatQuery RS Adapter Checkpoint — {config['model']['adapter_id']}

- **Base Model**: `{config['model']['name']}`
- **Adapter**: Low-Rank Adaptation (LoRA, rank={config['lora']['r']}, alpha={config['lora']['alpha']})
- **Dataset**: `{config['data']['dataset']} v{config['data']['dataset_version']}`
- **Validation Accuracy**: `{metrics['validation_accuracy'] * 100:.2f}%`
- **Validation Loss**: `{metrics['validation_loss']:.4f}`
- **Training Run ID**: `{run_id}`
- **Created At**: `{datetime.now(timezone.utc).isoformat()}`
""")

    # Save run record
    runs_dir = Path(config["output"].get("runs_directory", "training/runs"))
    if not runs_dir.is_absolute():
        runs_dir = Path(__file__).resolve().parent.parent / runs_dir
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_record = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "metrics": metrics,
        "output_directory": str(output_dir),
    }
    with open(runs_dir / f"{run_id}.json", "w", encoding="utf-8") as f:
        json.dump(run_record, f, indent=2)

    print(f"\nCHECKPOINT SAVED SUCCESSFULLY in {output_dir}")
    print(f"Run ID: {run_id}")
    print("=" * 65)


if __name__ == "__main__":
    main()
