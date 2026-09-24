# SatQuery AI Evaluation Framework Architecture

## 1. Architectural Overview

The **SatQuery AI Benchmark & Evaluation Engine** is an extensible, modular subsystem built in `evaluation/`. It decouples dataset adapters, task evaluators, standardized metrics, error taxonomies, and reporting generators:

```text
               ┌────────────────────────────────────────────────────────┐
               │              Benchmark Dataset Adapters                │
               │   VRSBench  │  RSVQA  │  CDVQA  │ BigEarthNet │ ISRO   │
               └───────────────────────────┬────────────────────────────┘
                                           │ yields BenchmarkSample
                                           ▼
┌─────────────────────────┐       ┌─────────────────────────────────────┐
│  Target Models / Agent  │ ----> │         Evaluation Runner           │
│   Specialist Predictors │       │  (Timing, Isolation, Prediction)   │
└─────────────────────────┘       └──────────────────┬──────────────────┘
                                                     │ yields ModelPrediction
                                                     ▼
                                  ┌─────────────────────────────────────┐
                                  │         Task Evaluators             │
                                  │ VQA │ Caption │ Grounding │ Change   │
                                  └──────────────────┬──────────────────┘
                                                     │
                                                     ▼
                                  ┌─────────────────────────────────────┐
                                  │ Standard Metrics & Error Taxonomy   │
                                  │   EM, F1, BLEU, IoU, ECE, Brier     │
                                  │      16-Class Error Taxonomy        │
                                  └──────────────────┬──────────────────┘
                                                     │
                                                     ▼
                                  ┌─────────────────────────────────────┐
                                  │     Reports & Artifacts Engine      │
                                  │  HTML Report │ Matrix JSON │ JSONL  │
                                  └─────────────────────────────────────┘
```

---

## 2. Core Components

### A. Normalized Sample Representation (`BenchmarkSample`)
Defined in `evaluation/core/sample.py`, `BenchmarkSample` standardizes inputs across all remote-sensing modalities:
- `sample_id`: Unique benchmark identifier.
- `task`: Standard task tag (`VQA`, `CAPTIONING`, `GROUNDING`, `CHANGE_VQA`, `CROSS_MODAL`, `ROUTING`).
- `inputs`: Dictionary holding `image` (optical), `image_t1` / `image_t2` (bi-temporal), or `sar` (microwave radar).
- `query`: Text question or instruction prompt.
- `reference`: Ground-truth dictionary holding answers, captions, bounding box regions, or change masks.
- `metadata`: Sensor specs, GSD, CRS, acquisition dates.

### B. Standardized Predictions (`ModelPrediction`)
Defined in `evaluation/core/prediction.py`:
- Captures `sample_id`, `model`, `task`, `answer`, `caption`, `regions`, `confidence`, and precise `latency_ms`.
- Records `confidence_method` and `is_adapted` flag.

### C. Standardized Error Taxonomy (16 Categories)
Defined in `evaluation/core/errors.py`:
Replaces vague error terms like "wrong" with precise diagnostic categories:
1. `INPUT_FAILURE`
2. `PAIR_VALIDATION_FAILURE`
3. `ALIGNMENT_FAILURE`
4. `WRONG_INTENT`
5. `WRONG_TOOL`
6. `WRONG_OBJECT`
7. `WRONG_LOCATION`
8. `WRONG_COUNT`
9. `WRONG_ATTRIBUTE`
10. `TEMPORAL_REASONING_ERROR`
11. `MODALITY_REASONING_ERROR`
12. `HALLUCINATION`
13. `INSUFFICIENT_EVIDENCE`
14. `LOW_CONFIDENCE`
15. `OVERCONFIDENT_ERROR`
16. `MODEL_FAILURE`

### D. Metrics Calculation Engine (`evaluation/core/metrics.py`)
- **Text & VQA:** Normalized Exact Match (EM), Token-level F1 score, Relaxed VQA Accuracy ($\text{F1} \ge 0.5$).
- **Scene Captioning:** BLEU 1–4 with brevity penalty, ROUGE-L with Longest Common Subsequence (LCS).
- **Visual Grounding:** Bounding box Intersection over Union (IoU), Recall@0.5, Precision@0.5.
- **Bi-Temporal Change:** Change mask IoU, Precision, Recall, and Dice F1.
- **Confidence Calibration:** Expected Calibration Error (ECE) with equal-width binning and Brier Score.

---

## 3. Execution CLI

The engine provides a standardized CLI entry point:

```bash
# Run all benchmarks and generate full HTML report
python -m evaluation.run --all

# Run specific task benchmarks
python -m evaluation.run --task vqa
python -m evaluation.run --task captioning
python -m evaluation.run --task grounding
python -m evaluation.run --task change
python -m evaluation.run --task routing
python -m evaluation.run --task calibration

# Limit evaluation to N samples per benchmark for rapid testing
python -m evaluation.run --all --limit 5
```

Artifacts are automatically produced in `artifacts/evaluation/`:
- `final_evaluation_report.html`: Self-contained interactive report with charts and scorecards.
- `evaluation_matrix.json`: Machine-readable summary for dashboards and APIs.
- Individual run directories containing `manifest.json` and `predictions.jsonl`.
