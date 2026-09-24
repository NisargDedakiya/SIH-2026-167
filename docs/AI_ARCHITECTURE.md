# SatQuery AI — Remote-Sensing AI Architecture (Phase 2)

## Architectural Principle

The SatQuery AI API never directly invokes or instantiates a concrete AI model:
```
Client / Dashboard (Next.js)
           ↓
FastAPI Endpoints (POST /api/v1/analysis/vqa, POST /api/v1/analysis/caption)
           ↓
AnalysisService (Lifecycle orchestration & DB persistence)
           ↓
AI ModelRuntime (Hardware device management, caching, lifecycle)
           ↓
ModelRegistry (Task resolution & capability metadata)
           ↓
SpecialistModel Adapter (validate → preprocess → predict → postprocess → confidence → evidence)
           ↓
Deep Learning Backbone (HuggingFace / PyTorch) or Mock Model (CI / offline)
```

This strict architectural separation ensures that when **Phase 3 Agentic Routing** is implemented, the agent router interacts directly with `AnalysisService` and `ModelRegistry` without needing to rewrite any Phase 2 inference or model code.

---

## Component Responsibilities

### 1. Specialist Model Interface (`SpecialistModel`)
Located in `backend/app/ai/base.py`. Every specialist AI model implements:
- `name: str`: Unique identifier (e.g. `remote-sensing-vqa`, `remote-sensing-caption`).
- `version: str`: Version string (e.g. `0.1.0`).
- `task: str`: Functional capability (`visual_question_answering`, `image_captioning`).
- `supported_modalities: List[str]`: List of compatible sensor modalities (`optical`, `multispectral`, `sar`).
- `validate_input(image_bytes, metadata)`: Ensures image is not corrupt and matches model modality.
- `preprocess(image_bytes, metadata)`: Extracts bands, normalizes dynamic range, and resizes to model input dimensions.
- `predict(processed_input, query=None)`: Performs the forward inference pass.
- `postprocess(raw_output)`: Converts raw logits/tensors into clean dictionary format.
- `confidence(raw_output)`: Calculates calibrated confidence with documented method.
- `evidence(raw_output)`: Extracts visual/token grounding evidence (empty list `[]` for Phase 2; spatial bounding boxes scheduled for Phase 4).

### 2. Model Registry (`ModelRegistry`)
Located in `backend/app/ai/registry.py`.
- `register(model, default_for_task=True)`: Registers a model instance.
- `get(name)`: Retrieves model by name.
- `get_by_task(task)`: Resolves default model for a given task.
- `list_models()`: Enumerates capabilities for API callers and the future Phase 3 agent router.

### 3. Model Runtime (`ModelRuntime`)
Located in `backend/app/ai/runtime.py`.
- **Lifecycle & Memory Management**: Models are loaded once and preserved in memory; never reloaded on every HTTP request.
- **Hardware Device Selection**: Inspects `AI_DEVICE` (`auto`, `cuda`, `cpu`). If CUDA is present and `auto` is specified, uses CUDA. Otherwise gracefully falls back to CPU without crashes.
- **Execution Instrumentation**: Wraps predictions with millisecond timing, logging, and error boundaries.

### 4. Remote-Sensing Preprocessing (`RemoteSensingPreprocessor`)
Located in `backend/app/ai/preprocessing.py`.
- **Non-Destructive**: Original satellite GeoTIFF is untouched in object storage.
- **Dynamic Bit-Depth Scaling**: Handles `uint8`, `uint16` (Sentinel-2, Landsat), and `float32` rasters.
- **Percentile Contrast Stretch**: Applies 2%-98% percentile clipping to handle atmospheric haze and extreme outliers.
- **Aspect-Preserving Resize**: Scales to model input (e.g. 384x384) with padding.

---

## Inference Lifecycle & State Progression

Every inference execution transitions through verified states in `analysis_jobs`:
```
QUEUED ──> VALIDATING ──> PREPROCESSING ──> RUNNING ──> POSTPROCESSING ──> COMPLETED
   │             │               │             │              │
   └─────────────┴───────────────┴─────────────┴──────────────┴───────> FAILED
```

1. **QUEUED**: Job record allocated with UUID in database.
2. **VALIDATING**: Image existence and modality checked against specialist model requirements.
3. **PREPROCESSING**: Raster downloaded from object store, bands selected, normalized.
4. **RUNNING**: Specialist model executes forward pass on CPU or CUDA.
5. **POSTPROCESSING**: Answer/caption extracted, confidence calibrated, evidence formatted.
6. **COMPLETED**: Result saved, duration recorded, returned to caller.
7. **FAILED**: Error captured in `error` column, HTTP 4xx/5xx returned without stack traces.

---

## AI Result Contract

All specialist models return the normalized contract:
```json
{
  "task": "visual_question_answering",
  "model": {
    "name": "remote-sensing-vqa",
    "version": "0.1.0"
  },
  "result": {
    "answer": "The scene primarily contains agricultural land with patches of dense vegetation."
  },
  "confidence": {
    "score": 0.8921,
    "method": "token_probability"
  },
  "evidence": [],
  "processing_time_ms": 340
}
```
