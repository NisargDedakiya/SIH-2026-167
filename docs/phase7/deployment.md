# Model Deployment & Operational Runtime Integration

## 1. Runtime Architecture
`satquery-rs-v1` is integrated natively into the SatQuery AI ModelRuntime:
1. **Model Registry Registration:** Automatically registered under task `visual_question_answering` as the **default** model.
2. **Agentic Router Preference:** When users pose analytical queries, the Agent Planner selects `SingleImageVQATool`, which dispatches to `satquery-rs-v1`.
3. **Trace Metadata:** Execution traces explicitly output:
   `✓ RS-adapted model selected: satquery-rs-v1 (Base: Salesforce/blip-vqa-base, Adapter: BigEarthNet-LoRA)`

---

## 2. Dynamic Memory Management & Lazy Loading
- **Memory Footprint:** 
  - Base Model: ~980 MB fp32 CPU RAM.
  - LoRA Adapter: ~6.3 MB weights loaded dynamically on demand.
- **Eager vs Lazy:** The model is registered at application startup and loaded into RAM on the first user query, preserving startup latency (< 1.5s).

---

## 3. Documented Automatic Fallback Mechanism
To ensure zero service downtime during deployments or missing weight scenarios:
1. **Detection:** When `RsAdaptedVqaModel.load()` is invoked, it verifies the existence of `artifacts/models/satquery-rs-adapter/adapter/adapter_model.bin`.
2. **Graceful Fallback:** If the adapter directory or weight file is missing or corrupted:
   - The runtime logs a warning: `Adapter checkpoint not found. Falling back to base model.`
   - The base generic VLM is loaded to handle user requests without throwing a 500 error.
   - The response metadata and execution trace clearly flag:
     `is_adapted: false`
     `fallback_used: true`
     `fallback_reason: "RS-adapted checkpoint unavailable, using base model"`
   - The frontend displays a cautionary amber badge:
     `Fallback: Base Model (RS-adapted checkpoint unavailable)`

---

## 4. REST API Endpoint Specifications

### 4.1 Enumerate Models (`GET /api/v1/analysis/models`)
Returns full capabilities, default task flags, and adaptation metadata.

### 4.2 Inspect Model Details (`GET /api/v1/analysis/models/{model_name}`)
Returns detailed architecture info, dataset provenance, and parameter counts.

### 4.3 Benchmark Metrics (`GET /api/v1/analysis/models/{model_name}/metrics`)
Returns empirical evaluation scores across VRSBench and RSVQA.
