# SatQuery AI — System Architecture Specification

**Project:** SatQuery AI  
**Scope:** Autonomous Vision-Language Assistant for Multimodal Remote Sensing Image Analysis  
**Specification:** ISRO / Smart India Hackathon Problem Statement 26167  
**Architecture Version:** 1.0.0 (Production Verified)

---

## 1. System Topology Overview

SatQuery AI is architectured as a multi-tier, decoupled geospatial and vision-language intelligence platform:

```mermaid
flowchart TD
    subgraph ClientTier["Client Tier (Presentation & Interaction)"]
        UI["Next.js 14 Web Application<br/>(App Router, React 18, TypeScript)"]
        DEMO["Demo Hub (/demo)<br/>Preset Canonical Scenarios"]
        WORKSPACES["Workspaces<br/>(/analyze, /temporal, /cross-modal)"]
        EVAL_DASH["Evaluation Dashboard (/evaluation)<br/>Matrix & Calibration"]
        REPORTS_VIEW["Report Viewer (/reports, /history)<br/>PDF, HTML, JSON, ZIP"]
    end

    subgraph GatewayTier["API Gateway Tier"]
        PROXY["Next.js Server Proxy / Rewrites<br/>(/api/v1/*, /health, /ready, /docs)"]
        FASTAPI["FastAPI Core Engine (Port 8000)<br/>Pydantic v2, CORS, Request ID Correlation"]
        MIDDLEWARE["Timing & Security Middleware<br/>X-Request-ID, Nosniff, Clickjacking Guard"]
    end

    subgraph CoreServices["Application Services Tier"]
        IMG_SVC["ImageService<br/>Ingestion, Validation, Previews"]
        ANALYSIS_SVC["AnalysisService<br/>VQA, Caption, Grounding, Evidence"]
        AGENT_SVC["SatQuery Agent Controller<br/>Classify, Resolve, Plan, Execute, Aggregate"]
        TEMP_SVC["TemporalService<br/>Alignment, Difference Maps, Change VQA"]
        CROSS_SVC["CrossModalService<br/>Optical/SAR Pairing, Log-Scaling, Dual-Stream Fusion"]
        EVAL_SVC["Evaluation Engine<br/>Benchmark Tasks, Metrics, Error Taxonomy"]
        REPORT_SVC["ReportGenerator<br/>ReportLab PDF, Interactive HTML, ZIP Bundler"]
    end

    subgraph GeospatialTier["Geospatial & Storage Infrastructure"]
        RASTER_ENGINE["Geospatial Engine<br/>Rasterio, GDAL, Affine Geotransforms, PyProj"]
        DB[(PostgreSQL 16 + PostGIS 3.4<br/>or SQLite Fallback)]
        OBJECT_STORE[(MinIO S3-Compatible Store<br/>or Local Disk Storage Fallback)]
    end

    subgraph AIRuntimeTier["AI / ML Specialist Model Runtime Tier"]
        MODEL_RUNTIME["ModelRuntime<br/>Device Selection (Auto, CUDA, CPU), Caching"]
        TOOL_REGISTRY["ToolRegistry<br/>9 Registered Specialist Analysis Tools"]
        BLIP_VQA["Salesforce/blip-vqa-base<br/>VQA Specialist"]
        ADAPTED_VQA["satquery-rs-v1<br/>BigEarthNet LoRA PEFT Adapter"]
        BLIP_CAPTION["blip-image-captioning-base<br/>Dense Scene Captioning"]
        OWLVIT["google/owlvit-base-patch32<br/>Open-Vocabulary Spatial Grounding"]
        SIAM_DIFF["Remote-Sensing Siamese Diff<br/>Bi-Temporal Pixel Alignment & Masks"]
        SAR_FUSION["Optical-SAR Fusion Specialist<br/>Decibel Log-Scaling & Joint Reasoning"]
    end

    UI --> PROXY
    DEMO --> PROXY
    WORKSPACES --> PROXY
    EVAL_DASH --> PROXY
    REPORTS_VIEW --> PROXY

    PROXY --> FASTAPI
    FASTAPI --> MIDDLEWARE

    MIDDLEWARE --> IMG_SVC
    MIDDLEWARE --> ANALYSIS_SVC
    MIDDLEWARE --> AGENT_SVC
    MIDDLEWARE --> TEMP_SVC
    MIDDLEWARE --> CROSS_SVC
    MIDDLEWARE --> EVAL_SVC
    MIDDLEWARE --> REPORT_SVC

    IMG_SVC --> RASTER_ENGINE
    IMG_SVC --> DB
    IMG_SVC --> OBJECT_STORE

    ANALYSIS_SVC --> MODEL_RUNTIME
    ANALYSIS_SVC --> DB
    ANALYSIS_SVC --> OBJECT_STORE

    AGENT_SVC --> TOOL_REGISTRY
    TOOL_REGISTRY --> MODEL_RUNTIME
    AGENT_SVC --> DB

    TEMP_SVC --> RASTER_ENGINE
    TEMP_SVC --> MODEL_RUNTIME
    TEMP_SVC --> DB

    CROSS_SVC --> RASTER_ENGINE
    CROSS_SVC --> MODEL_RUNTIME
    CROSS_SVC --> DB

    REPORT_SVC --> DB
    REPORT_SVC --> OBJECT_STORE

    MODEL_RUNTIME --> BLIP_VQA
    MODEL_RUNTIME --> ADAPTED_VQA
    MODEL_RUNTIME --> BLIP_CAPTION
    MODEL_RUNTIME --> OWLVIT
    MODEL_RUNTIME --> SIAM_DIFF
    MODEL_RUNTIME --> SAR_FUSION
```

---

## 2. Ingestion & Geospatial Request Lifecycle

When a remote-sensing raster file is submitted to `POST /api/v1/images/upload`:

```mermaid
sequenceDiagram
    autonumber
    actor User as Client / User
    participant GW as Next.js Proxy / FastAPI
    participant Sec as Geospatial Validator
    participant RS as SafeRasterReader
    participant Meta as MetadataExtractor
    participant Prev as PreviewGenerator
    participant Store as ObjectStore (MinIO/Local)
    participant DB as Database (Postgres/SQLite)

    User->>GW: POST /api/v1/images/upload (multipart/form-data)
    GW->>Sec: Validate File Extension & Magic Bytes
    alt Invalid format or magic bytes mismatch
        Sec-->>GW: Raise HTTPException(400, "Unsupported file format")
        GW-->>User: 400 Bad Request
    end
    Sec->>Sec: Enforce Decompression Bomb Limits (<= 8192px, <= 500MB)
    GW->>RS: SafeRasterReader.open_bytes(file_bytes)
    RS->>Meta: Extract dimensions, bands, dtype, nodata, CRS, transform, bounds
    RS->>Prev: Generate 2%–98% percentile-stretched RGB preview (<= 2048px PNG)
    GW->>Store: upload_bytes("images/{uuid}/original.tif", raw_bytes)
    GW->>Store: upload_bytes("images/{uuid}/preview.png", preview_bytes)
    GW->>DB: INSERT into images & image_metadata (atomic commit)
    DB-->>GW: Commit confirmed
    GW-->>User: 201 Created (ImageUploadResponse: id, filename, status, bounds, crs)
```

---

## 3. Agentic Query Request Lifecycle

When a natural-language query is submitted to `POST /api/v1/agent/analyze`:

```mermaid
sequenceDiagram
    autonumber
    actor User as Client / User
    participant Router as Agent API Router
    participant Norm as QueryNormalizer
    participant Clf as QueryClassifier
    participant Res as CapabilityResolver
    participant Plan as WorkflowPlanner
    participant Exec as ToolExecutor
    participant Tool as Registered Specialist Tool
    participant Runtime as ModelRuntime
    participant Agg as ResultAggregator
    participant Trace as ExecutionTraceContext
    participant DB as Database

    User->>Router: POST /api/v1/agent/analyze {query, image_ids, context}
    Router->>Trace: Initialize trace (agent_run_id, correlation_id)
    Trace->>Trace: Emit event: "query_received"
    Router->>Norm: normalize(query)
    Norm-->>Clf: Cleaned query text
    Router->>Clf: classify(query, input_context)
    Clf-->>Router: ClassificationResult (intent, confidence, reasoning)
    Trace->>Trace: Emit event: "intent_classified"

    alt Query is AMBIGUOUS
        Router-->>User: Return 200 OK with clarification prompt
    end

    Router->>Res: resolve_capability(intent, input_context)
    alt Incompatible inputs (e.g. 1 image for temporal change)
        Res-->>Router: CapabilityResolution(status="unavailable", error_reason)
        Router-->>User: Return 200/400 with structured capability failure
    end

    Router->>Plan: create_plan(task, tool, query, input_context)
    Plan-->>Router: WorkflowPlanSchema (steps, parameters)
    Trace->>Trace: Emit event: "plan_generated"

    Router->>Exec: execute_plan(plan, input_context, db)
    Exec->>Tool: execute(input_context, parameters, db)
    Tool->>Runtime: execute(model, image_bytes, metadata, query)
    Runtime-->>Tool: Raw model output contract
    Tool-->>Exec: Standardized tool result contract
    Exec-->>Router: Step outputs & tool execution metrics
    Trace->>Trace: Emit event: "tool_executed"

    Router->>Agg: aggregate_results(query, plan, execution_results)
    Agg->>Agg: Compute calibrated confidence score
    Agg->>Agg: Classify observations (observed, inferred, uncertain)
    Agg-->>Router: Harmonized agent answer payload
    Trace->>Trace: Emit event: "aggregation_complete"

    Router->>DB: Persist AgentRunModel & AgentTraceEventModel
    Router-->>User: 200 OK (AgentAnalyzeResponse: answer, observations, confidence, trace)
```

---

## 4. Layer Responsibilities & Source Code Traceability

| Architectural Layer | Repository Path | Primary Modules | Core Responsibilities |
| :--- | :--- | :--- | :--- |
| **Frontend Application** | `frontend/` | `app/page.tsx`, `app/demo/`, `app/analyze/`, `components/` | Client-side routing, interactive satellite imagery viewing, canvas bounding box rendering, bitemporal split-screen comparison, optical-SAR dual viewing, multi-format report exports. |
| **API Gateway & Routing** | `backend/app/api/` | `__init__.py`, `health.py`, `images.py`, `analysis.py`, `agent.py`, `temporal.py`, `cross_modal.py`, `evaluation.py`, `reports.py` | FastAPI endpoint definitions, input parameter validation, dependency injection (`get_db`), HTTP error code mapping, response serialization. |
| **Geospatial Processing Engine** | `backend/app/geospatial/` | `reader.py`, `metadata.py`, `normalization.py`, `preview.py`, `validator.py` | Rasterio-based safe reading, native CRS and affine geotransform extraction, high-dynamic-range radiometric stretching (2%–98%), browser-friendly preview creation, decompression bomb defenses. |
| **Agentic Controller** | `backend/app/agent/` | `controller.py`, `classifier.py`, `resolver.py`, `planner.py`, `executor.py`, `aggregator.py`, `trace.py` | Query normalization, hybrid keyword/regex/context intent classification, deterministic capability resolution, sandboxed tool dispatch, observation categorization, execution trace collection. |
| **Tool Registry** | `backend/app/tools/` | `registry.py`, `base.py`, `vqa.py`, `caption.py`, `grounding.py`, `change_detection.py`, `change_vqa.py`, `change_description.py`, `optical_sar_analysis.py`, `optical_sar_vqa.py`, `optical_sar_grounding.py` | Explicit registration of 9 verified analysis tools, input pre-validation, task indexing, sandboxed execution without arbitrary code execution. |
| **AI Specialist Runtime** | `backend/app/ai/` | `runtime.py`, `registry.py`, `base.py`, `preprocessing.py`, `postprocessing.py`, `models/` | Hardware device auto-detection (`cuda` vs `cpu`), model lifecycle management, in-memory model caching, execution timing instrumentation, graceful fallback to base models if checkpoints are missing. |
| **Temporal Change Engine** | `backend/app/temporal/` | `alignment.py`, `change_map.py`, `change_vqa.py`, `compatibility.py`, `description.py`, `regions.py`, `service.py`, `validator.py` | Pair registration ($T_1 < T_2$), spatial overlap calculation, bilinear grid resampling, difference matrix generation, change percentage calculation, connected component polygonization. |
| **Cross-Modal Fusion Engine** | `backend/app/cross_modal/` | `alignment.py`, `compatibility.py`, `fusion.py`, `reasoning.py`, `service.py`, `validator.py` | Optical vs. SAR modality detection, log-scale decibel backscatter normalization, dual-stream feature fusion, joint observation synthesis, sensor conflict/disagreement detection. |
| **Evidence Engine** | `backend/app/evidence/` | `artifacts.py`, `geometry.py`, `overlay.py`, `renderer.py` | Bounding box normalization $[ymin, xmin, ymax, xmax]$, pixel-to-geographic coordinate reprojection, binary mask generation, visual overlay rendering, evidence crop artifact storage. |
| **Storage Layer** | `backend/app/storage/` | `object_store.py`, `exceptions.py` | Abstract `ObjectStore` interface supporting MinIO (S3-compatible) and local filesystem fallback, path traversal defense, typed `StorageObjectNotFoundError`. |
| **Database Tier** | `backend/app/database/` | `models.py`, `session.py`, `alembic/` | PostgreSQL 16 with PostGIS 3.4 (with SQLite fallback for local dev), 8 SQLAlchemy async models, self-healing startup column synchronization, Alembic migration scripts. |
| **Report Engine** | `backend/app/reports/` | `generator.py`, `pdf_exporter.py`, `html_exporter.py`, `json_exporter.py`, `package_exporter.py` | Compiles analysis records, metadata, evidence crops, and execution traces into formal vector PDF (ReportLab), self-contained interactive HTML, machine-readable JSON, and deliverable ZIP bundles. |
| **Evaluation Framework** | `evaluation/` | `run.py`, `compare.py`, `core/`, `datasets/`, `tasks/` | Multi-dataset benchmark harness (BigEarthNet, VRSBench, RSVQA, CDVQA, ISRO/SAC), standard metric calculations (EM, F1, BLEU-4, ROUGE-L, IoU, ECE, Brier Score), zero fabrication reporting. |
| **Domain Adaptation Pipeline** | `training/` | `train_rs_adapter.py`, `peft_adapter.py`, `adapter_validation.py`, `configs/rs_adapter.yaml` | BigEarthNet v2.0 dataset loader, PEFT/LoRA fine-tuning for Vision-Language Models, data leakage quarantine, adapter checkpoint generation (`artifacts/models/satquery-rs-adapter`). |

---

## 5. Security & Isolation Architecture

1. **Path Traversal Guard:**
   - User-supplied filenames are never used as physical storage keys.
   - Storage keys strictly follow randomized UUID schemes: `images/{uuid}/original.tif`, `images/{uuid}/preview.png`, `evidence/{uuid}/crop.png`.
   - The storage layer resolves paths against the canonical base directory and asserts that resolved paths begin with the base directory path.

2. **Decompression Bomb Defense:**
   - Maximum upload size is strictly capped at `MAX_UPLOAD_SIZE_MB` (default 500 MB).
   - Raster dimensions are verified before uncompressed allocation: width and height must not exceed 8,192 pixels, and total uncompressed pixel count must not exceed 67,108,864 pixels.

3. **Deterministic Sandbox Execution:**
   - The agentic controller dispatches requests strictly to pre-registered instances in `ToolRegistry`.
   - No Python `eval()`, `exec()`, or sub-shell invocation exists anywhere in the agent dispatch pipeline.

4. **Masked Internal Errors:**
   - Unhandled server exceptions are trapped by global FastAPI handlers and converted to structured JSON envelopes.
   - Database credentials, internal file paths, and raw stack traces are masked, returning only a unique `trace_id` for administrative log correlation.
