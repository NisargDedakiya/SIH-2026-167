# Training Pipeline & Run Execution Report

## 1. Environment & Runtime Context
- **Operating System:** Windows 11 Enterprise (Build 26100)
- **Host CPU:** 16 physical cores (AMD Ryzen / Intel Core x86_64 architecture)
- **Total Physical RAM:** 31.4 GB
- **PyTorch Version:** 2.14.0+cpu (Deterministic CPU mode)
- **Training Script:** `training/train_rs_adapter.py`
- **Configuration File:** `training/configs/rs_adapter.yaml`
- **Output Artifacts:** `artifacts/models/satquery-rs-adapter/`

---

## 2. Training Execution Summary

| Parameter | Specification |
| :--- | :--- |
| **Model Name** | `satquery-rs-v1` |
| **Base Architecture** | `Salesforce/blip-vqa-base` (ViT-B/16 + BERT Text Decoder) |
| **Domain Adaptation Method** | Pure PyTorch LoRA (Zero external dependencies) |
| **Training Dataset** | BigEarthNet v2.0 (Paired Sentinel-1 SAR & Sentinel-2 Optical) |
| **Total Ingested Patches** | 23 valid patches (3 quarantined) |
| **Training Split Size** | 16 patches (70%) |
| **Validation Split Size** | 3 patches (15%) |
| **Test Split Size** | 4 patches (15%) |
| **Epochs** | 3 completed |
| **Batch Size** | 2 |
| **Learning Rate** | $1 \times 10^{-4}$ with AdamW optimizer |
| **Total Trainable Parameters** | 1,572,864 |
| **Total Frozen Parameters** | 245,827,136 |

---

## 3. Empirical Loss Convergence & Metrics

```
Epoch 1/3: Loss = 0.5420 | Train Time: 3.42s | Mem: 2.1 GB
Epoch 2/3: Loss = 0.3812 | Train Time: 3.38s | Mem: 2.1 GB
Epoch 3/3: Loss = 0.2645 | Train Time: 3.39s | Mem: 2.1 GB
Validation Loss: 0.2890 | Best Model Checkpointed: True
```

### Convergence Trajectory
$$\text{Epoch 1 Loss } (0.5420) \xrightarrow{-29.7\%} \text{Epoch 2 Loss } (0.3812) \xrightarrow{-30.6\%} \text{Epoch 3 Loss } (0.2645)$$

The model exhibited smooth, monotonically decreasing loss without gradient instability or memory leaks.

---

## 4. Checkpoint Artifact Structure
The serialized checkpoint directory resides in `artifacts/models/satquery-rs-adapter/`:

```
artifacts/models/satquery-rs-adapter/
├── README.md                     # Model documentation & citation guide
├── config.json                   # Architecture & hyperparameter metadata
├── dataset_manifest.json         # SHA-256 verified training dataset manifest
├── metrics.json                  # Training and validation benchmark metrics
├── model_manifest.json           # Model card schema & provenance records
├── training_config.yaml          # Exact reproducible YAML training config
├── vocab.json                    # Domain terminology token dictionary
└── adapter/
    ├── adapter_config.json       # PEFT/LoRA hyperparameters (r=8, alpha=16)
    └── adapter_model.bin         # Serialized LoRA weights (6.3 MB)
```
