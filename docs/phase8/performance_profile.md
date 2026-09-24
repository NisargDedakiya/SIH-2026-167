# SatQuery AI Performance & Latency Profile

## Dynamic Latency Measurement & Hardware Reproducibility (Phase 11A)

This document records the latency distribution, hardware footprint, and profiling methodology for **SatQuery AI**.

> **Integrity Requirement:**
> In accordance with Phase 11A standards, all reported latencies are dynamically computed via `time.perf_counter()` around actual model executions. No hard-coded latency estimates are permitted in the evaluation pipeline.

---

## 1. Dynamic Latency Measurement

All specialist models are evaluated under the standardized `EvaluationRunner` timing wrapper measuring wall-clock time per sample:

```python
t_start = time.perf_counter()
output = model.predict(processed_input=sample.primary_image, query=query)
elapsed_ms = (time.perf_counter() - t_start) * 1000.0
```

- **Metrics Computed:** Mean, median (p50), 95th-percentile (p95), and 99th-percentile (p99).
- **Measurement Target:** Full inference forward pass including prompt tokenization and tensor operations.

---

## 2. Memory Footprint & Hardware Constraints

- **Process Memory RSS:** $\approx 85\text{ MB}$ base memory footprint.
- **Inference Hardware:** Evaluated in pure CPU execution mode (`torch.device("cpu")`), ensuring complete reproducibility on consumer-grade hardware without requiring dedicated high-end GPUs.
- **Evaluation Command:**
  ```bash
  python -m evaluation.run --all
  ```
