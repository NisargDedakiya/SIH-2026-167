# SatQuery AI — Final System Architecture

**Project:** SatQuery AI  
**Scope:** Autonomous Vision-Language Assistant for Multimodal Remote Sensing Image Analysis  
**Specification:** ISRO / Smart India Hackathon Problem Statement 26167  
**Architecture Version:** 1.0.0 (Production Hardened)

---

## 1. System Topology Overview

```text
                               ┌────────────────────────────────┐
                               │     USER / JUDGES / RESEARCH   │
                               └───────────────┬────────────────┘
                                               │
                                      HTTP / JSON / REST
                                               │
               ┌───────────────────────────────▼───────────────────────────────┐
               │                  NEXT.JS 14 FRONTEND SPA                      │
               │  ┌────────────┬─────────────┬─────────────┬────────────────┐  │
               │  │  Dashboard │  Demo Hub   │  Analysis   │ Reports & Lib  │  │
               │  │  (Overview)│   (/demo)   │  Workspace  │  (Multi-Export)│  │
               │  └────────────┴─────────────┴─────────────┴────────────────┘  │
               │  ┌──────────────────────────┬──────────────────────────────┐  │
               │  │ Evidence Viewer Unified  │ Evaluation Benchmark Matrix  │  │
               │  └──────────────────────────┴──────────────────────────────┘  │
               └───────────────────────────────┬───────────────────────────────┘
                                               │
                                      Reverse Proxy / CORS
                                               │
               ┌───────────────────────────────▼───────────────────────────────┐
               │                    FASTAPI API GATEWAY                        │
               │  ┌─────────────────────────────────────────────────────────┐  │
               │  │ Liveness (/health) & Deep Dependency Readiness (/ready) │  │
               │  ├─────────────────────────────────────────────────────────┤  │
               │  │ Standardized Error Handler (Code, Msg, Details, TraceID)│  │
               │  ├─────────────────────────────────────────────────────────┤  │
               │  │ Request ID / Correlation Context & Timing Middleware    │  │
               │  └─────────────────────────────────────────────────────────┘  │
               └───────────────────────────────┬───────────────────────────────┘
                                               │
          ┌────────────────────────────────────┼────────────────────────────────────┐
          │                                    │                                    │
┌─────────▼─────────┐               ┌──────────▼──────────┐              ┌──────────▼──────────┐
│   DATABASE TIER   │               │   OBJECT STORAGE    │              │   AGENT & AI CORE   │
│                   │               │                     │              │                     │
│ PostgreSQL 16     │               │ MinIO S3-Compatible │              │ SatQuery Agent      │
│ PostGIS Spatial   │               │ Local Filesystem    │              │ Model Runtime       │
│ SQLAlchemy Async  │               │ UUID-Isolated Keys  │              │ Tool Registry       │
└───────────────────┘               └─────────────────────┘              └──────────┬──────────┘
                                                                                    │
               ┌────────────────────────────────────────────────────────────────────┴────────────────┐
               │                                                                                     │
     ┌─────────▼─────────┐                                                                 ┌─────────▼─────────┐
     │  SPECIALIST TOOLS │                                                                 │  EVIDENCE & EVAL  │
     │                   │                                                                 │                   │
     │ • Single VQA      │                                                                 │ • Evidence Engine │
     │ • Captioning      │                                                                 │ • Confidence Mod  │
     │ • Grounding       │                                                                 │ • Benchmark Eval  │
     │ • Temporal Change │                                                                 │ • ReportLab PDF   │
     │ • Optical + SAR   │                                                                 │ • ZIP Packager    │
     └───────────────────┘                                                                 └───────────────────┘
```

---

## 2. Ingestion & Geospatial Data Pipeline

```text
User File Upload
  │
  ▼
[1] Extension & MIME Sniffing
  ├── Reject unauthorized extensions (.py, .sh, .exe)
  └── Magic byte verification (TIFF, BigTIFF, PNG, JPEG)
  │
  ▼
[2] Decompression Bomb Defense
  ├── Max dimension check: <= 8192 px
  └── Max pixel count check: <= 67.1M pixels
  │
  ▼
[3] Rasterio / GDAL Metadata Extraction
  ├── Preserve native CRS (e.g. EPSG:32643, UTM, geographic)
  ├── Extract native affine geotransform & pixel resolution
  └── Compute dynamic NoData mask & radiometric bounds
  │
  ▼
[4] Parallel Persistence
  ├── Primary raster uploaded with randomized UUID key: images/{id}/original.tif
  ├── Optimized browser PNG preview generated: images/{id}/preview.png
  └── Metadata & geospatial spatial bounding box written to PostgreSQL / SQLite
```

---

## 3. Agentic Routing & Sandboxed Execution Pipeline

```text
User Natural-Language Query
  │
  ▼
[1] Normalization: Collapse whitespace, remove formatting noise, lower-case tokens
  │
  ▼
[2] Intent Classification:
    • Question syntax & land cover keywords       ──> VISUAL_QUESTION_ANSWERING
    • "Describe scene", "caption", "overview"      ──> SCENE_DESCRIPTION
    • "Highlight", "locate", "outline", "where"    ──> GROUNDING
    • "What changed", "areas changed", "dates"     ──> CHANGE_ANALYSIS
    • "Optical and SAR", "fuse", "radar"           ──> CROSS_MODAL_ANALYSIS
    • Unspecified / broad queries ("tell me...")   ──> AMBIGUOUS (Prompt for clarification)
  │
  ▼
[3] Capability Resolution:
    • Verify image count matches task (Temporal >= 2, Cross-modal >= 2)
    • Verify tool exists in ToolRegistry
    • Fail closed with status="unavailable" if unsupported (Zero silent fallbacks)
  │
  ▼
[4] Workflow Planning & Sandboxed Dispatch:
    • Formulate strict parameter dictionary
    • Dispatch via registered ToolExecutor (No dynamic eval() or shell execution)
  │
  ▼
[5] Result Aggregation & Harmonization:
    • Calibrate probabilistic confidence score
    • Categorize findings into Tripartite Taxonomy: OBSERVED, INFERRED, UNCERTAIN
    • Emit complete observable execution trace with timestamped micro-milestones
```

---

## 4. Multimodal Analysis Subsystems

### 4.1 Single-Image Intelligence
- **VQA & Captioning:** Leverages remote-sensing adapted vision-language models to answer queries regarding scene contents, urban density, vegetation health, and infrastructure.
- **Spatial Grounding:** Maps text referring expressions to normalized bounding boxes $[ymin, xmin, ymax, xmax]$, subsequently reprojected to native UTM coordinates and rendered as visual evidence overlays.

### 4.2 Bi-Temporal Change Intelligence
- **Temporal Ordering:** Asserts $T_1 < T_2$.
- **Spatial Co-Registration:** Computes spatial intersection ratio; verifies pixel grid alignment.
- **Change Extraction:** Generates pixel difference maps, computes changed surface percentage, and isolates connected change polygon regions.

### 4.3 Optical + SAR Cross-Modal Fusion
- **Modality Detection:** Validates presence of complementary optical (Sentinel-2 / Cartosat) and SAR (Sentinel-1 / RISAT) rasters.
- **Dual-Stream Processing:** Optical undergoes spectral reflectance normalization; SAR undergoes decibel log-scale normalization to preserve specular scatter.
- **Cross-Modal Reasoning:** Reports joint observations, optical-specific insights, SAR-specific penetration, and explicit modality disagreements.

---

## 5. Security & Reliability Architecture

1. **Path Traversal Prevention:** Storage paths strictly derive from internal UUIDs; client filenames are stripped of directories (`../`), absolute slashes, and null bytes.
2. **Zero Fabrication Policy:** All confidence metrics, evaluation benchmarks, and change statistics derive from empirical calculations; no canned or synthetic numbers are returned.
3. **Graceful Failures:** Failures in raster alignment, evidence rendering, or report compilation emit standardized error payloads with unique trace IDs and masked internal stack traces.
4. **Deployability:** Multi-profile Docker containers support instant evaluation on both GPU-accelerated servers and CPU-only laptops.
