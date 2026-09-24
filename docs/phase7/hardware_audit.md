# Phase 7: Hardware & Environment Audit

## 1. System Hardware Specifications

| Component | Detected Specification | Operating Status |
|---|---|---|
| **Operating System** | Windows 11 Pro (`10.0.26200-SP0`) | Active / Native |
| **CPU Architecture** | 16 Physical Cores / 16 Logical Threads | Verified High Multi-core Throughput |
| **System Memory (RAM)** | 31.36 GB Available | High Capacity (Supports in-memory batching) |
| **Disk Storage** | 501.59 GB Free Space | Ample capacity for dataset caches & checkpoints |
| **GPU / Accelerators** | None / Discrete GPU Unreachable | CUDA Available: `False` |
| **PyTorch Version** | `2.14.0+cpu` | CPU Execution Mode |

---

## 2. Resource Constraints & Mitigation Strategy

1. **No High-End Dedicated Cloud GPU**:
   - Training a multi-billion parameter foundation VLM from scratch is neither feasible nor technically sound for domain adaptation.
   - **Mitigation**: Parameter-Efficient Fine-Tuning (PEFT / LoRA / Adapter heads). Only adapter weights ($\approx 0.5\% - 2\%$ of parameters) are updated, freezing the foundational vision-language backbone.
2. **Memory & Compute Budgeting**:
   - Recommended Training Mode: **CPU-Optimized Parameter-Efficient Training (PEFT)**.
   - Batch Size: `2` to `4` samples per step.
   - Gradient Accumulation: `4` steps (effective batch size of `8`–`16`).
   - Mixed Precision: `fp32` (stable CPU numerical precision).
   - Epochs / Max Steps: Controlled training budget with early validation checkpointing.
3. **Inference Decoupling**:
   - Production inference must preserve `AI_DEVICE=auto`, `AI_DEVICE=cpu`, `AI_DEVICE=cuda` flexibility.
   - Inference latency on CPU must remain interactive ($\le 1.5\text{s}$ per query).
