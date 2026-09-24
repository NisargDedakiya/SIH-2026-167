# Prototype Model Artifact — LightweightRSVLM (CPU Smoke-Test)

> [!WARNING]
> **DEVELOPMENT PROTOTYPE ONLY — NOT OFFICIAL BLIP ADAPTER**
> This checkpoint was produced by `LightweightRSVLM-Prototype-256d` for development pipeline validation, shape checking, and CPU smoke testing.
> It is **NOT** compatible with `Salesforce/blip-vqa-base` and **MUST NOT** be used as the official `satquery-rs-v1` adapter.

## Prototype Overview
- **Architecture**: `LightweightRSVLM-256d` (Conv2d patch projection + MultiheadAttention + Linear LM Head)
- **Base Model**: Custom lightweight PyTorch module (256-dim, 4 heads)
- **Adapter Type**: LoRA ($r=8, \alpha=16$)
- **Target Modules**: `feed_forward`, `lm_head`
- **Training Status**: `development_prototype`
- **Dataset Partition**: BigEarthNet synthetic smoke-test sample partition (50 steps)
- **Validation Loss**: 7.0479
- **Validation Accuracy**: 0.0%

## Provenance
This artifact is preserved for architectural regression testing, LoRA parameter injection unit tests, and verifying that the runtime correctly detects and rejects mismatched checkpoints.
