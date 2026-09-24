# SatQuery AI — Phase 9 Product UX & Report Engine Guide

**ISRO Smart India Hackathon · Problem Statement 26167**  
*Interactive Remote-Sensing Vision-Language Assistant*

---

## 1. Executive Summary

Phase 9 transforms **SatQuery AI** from developer-oriented endpoints into an interactive, publication-grade, accessible web product. It establishes:

1. **A Single Authoritative Report Schema (`AnalysisReport`)**: Drives JSON, HTML, PDF, and ZIP deliverables from the same normalized data representation (Zero Fabrication).
2. **Multi-Format Export Engine**:
   - **Interactive HTML**: Standalone, fully styled, responsive document viewable in any modern browser offline.
   - **Formal Vector PDF**: Publication-grade printable report generated via ReportLab with ISRO SIH title blocks, metadata grids, observation tiers, and reproducibility tokens.
   - **Machine-Readable JSON**: Complete schema for GIS pipeline automation and programmatic validation.
   - **Deliverable ZIP Archive**: Sanitized package bundling all reports, evidence raster maps, audit trace logs, and manifest documentation.
3. **Interactive Frontend Workspaces**:
   - **Dashboard (`/`)**: High-level overview, quick actions, Hackathon Demo Gallery, and recent activity feed.
   - **Unified Analysis Workspace (`/analyze`)**: Ingestion inspector, sensor compatibility checks, domain query prompts, real-time milestone stepper, and evidence visualization.
   - **Stable Analysis Route (`/analysis/[id]`)**: Full deep reconstruction from persistent database entities surviving browser refreshes.
   - **Audit History (`/history`)**: Filterable, searchable, paginated activity log.
   - **Reports Library (`/reports`)**: Centralized download center for verified intelligence deliverables.
   - **Image Catalog (`/images`)**: Geospatial data lake browser with metadata inspectors and quick-analysis routing.

---

## 2. Architecture & Export Pipeline

```
              ┌────────────────────────────────────────────────────────┐
              │              Analysis Execution Event                  │
              │  (VQA / Grounding / Bi-Temporal / Optical-SAR Fusion)  │
              └───────────────────────────┬────────────────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    Database Persistence Layer         │
                      │  - AnalysisJobModel                   │
                      │  - ImageModel / BiTemporal / OptSAR   │
                      │  - EvidenceModel (BBoxes, GeoJSON)    │
                      │  - AgentRunModel & TraceEventModel    │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    ReportGenerator (Zero Fabrication) │
                      │  Reconstructs authoritative entity    │
                      │         AnalysisReport                │
                      └───────────────────┬───────────────────┘
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 │                        │                        │
                 ▼                        ▼                        ▼
     ┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
     │   JsonReportExporter  │ │   HtmlReportExporter  │ │   PdfReportExporter   │
     │   (Machine JSON)      │ │   (Interactive HTML)  │ │   (ReportLab Vector)  │
     └───────────┬───────────┘ └───────────┬───────────┘ └───────────┬───────────┘
                 │                         │                         │
                 └─────────────────────────┼─────────────────────────┘
                                           │
                                           ▼
                            ┌───────────────────────────────┐
                            │    AnalysisPackageExporter    │
                            │  Compiles sanitized .zip with │
                            │  reports, traces, & evidence  │
                            └───────────────────────────────┘
```

---

## 3. Normalized Report Schema (`AnalysisReport`)

Defined in `backend/app/reports/schemas.py`:

| Component | Class | Description |
| :--- | :--- | :--- |
| **Core Metadata** | `AnalysisReport` | Report ID, analysis ID, timestamp, task type, question, answer, confidence, token |
| **Input Ingestion** | `ReportInputImage` | Geospatial specs: dimensions, bands, sensor, CRS, GSD resolution, validation |
| **Visual Evidence** | `ReportEvidenceItem` | Bounding boxes (pixel & CRS), area in m², evidence type, confidence |
| **Observations** | `ReportObservations` | Three-tier breakdown: Observed Facts, Model Inferences, Uncertain Cues |
| **Model Details** | `ReportModelDetails` | Base model, adapter (LoRA BigEarthNet), quantization, hardware runtime |
| **Execution Steps**| `ReportExecutionMilestone` | Milestone name, sequence, timing (ms), completion status |

---

## 4. API Endpoints Reference

All endpoints conform to FastAPI standards and are mounted under `/api/v1/`:

| Method | Path | Content-Type | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/reports/{id}` | `application/json` | Retrieves high-level report metadata & schema summary |
| `GET` | `/api/v1/reports/{id}/json` | `application/json` | Downloads raw, formatted `AnalysisReport` JSON |
| `GET` | `/api/v1/reports/{id}/html` | `text/html` | Streams styled, self-contained standalone HTML report |
| `GET` | `/api/v1/reports/{id}/pdf` | `application/pdf` | Streams publication-grade printable vector PDF |
| `GET` | `/api/v1/reports/{id}/package` | `application/zip` | Downloads deliverable ZIP archive with all assets |
| `GET` | `/api/v1/analysis/history` | `application/json` | Paginated search across past jobs (`?task=`, `?status_filter=`, `?search=`) |
| `GET` | `/api/v1/analysis/{id}` | `application/json` | Deep reconstruction of analysis job, evidence, and traces |

---

## 5. Frontend Product Pages

### 5.1 Dashboard (`/`)
- Hero section highlighting SIH Problem Statement 26167 and Phase 9 Product UX.
- One-click **Demo Gallery** with pre-configured prompts:
  1. *Remote-Sensing VQA* (BigEarthNet LoRA adapted)
  2. *Text-Guided Grounding* (VRSBench bounding box locator)
  3. *Bi-Temporal Change Detection* (CDVQA multi-epoch comparison)
  4. *Optical + SAR Cross-Modal Fusion* (Cartosat-2S & RISAT joint interpretation)
  5. *Benchmark Evaluation Engine* (Reproducible metrics & ECE calibration)
- Live database feed of recent analyses with confidence badges and deep links.

### 5.2 Unified Analysis Workspace (`/analyze`)
- Ingested image picker and quick-upload drawer.
- Automatic **Input Inspector** (CRS, GSD resolution, band count).
- Real-time **Compatibility Status** checker (checks receptive field, radiometric scaling, CRS projection).
- Task selector (VQA, Grounding, Captioning) with domain-specific suggested prompts.
- Live progress stepper displaying milestones as they execute.
- Direct output showing answers, confidence ratings, bounding box overlays, model specs, and export action bar.

### 5.3 Stable Detail Route (`/analysis/[id]`)
- Fully reconstructs analysis results from database storage.
- Survives browser refreshes and bookmarking.
- Interactive multi-modal viewer supporting single images with zoom/pan, bi-temporal swipe splits, and optical-SAR side-by-side viewports.
- Export toolbar for direct 1-click downloading of HTML, PDF, JSON, and ZIP packages.

### 5.4 Audit History (`/history`)
- Real-time search by prompt, answer text, or job UUID.
- Filtering by task type (VQA, Grounding, Captioning, Temporal, Cross-Modal) and execution status.
- Pagination controls with total record count and duration indicators.

### 5.5 Reports Library (`/reports`)
- Catalog of all completed analysis jobs with direct action buttons for HTML, PDF, and ZIP packages.
- Overview of deliverable standards and validation guarantees.

### 5.6 Satellite Image Catalog (`/images`)
- Geospatial raster data lake with thumbnails, format badges (GeoTIFF, TIFF, PNG, JPEG), dimensions, bands, and CRS info.
- Quick "Analyze This Image" shortcut button directing to the `/analyze` workspace.

---

## 6. Verification & Quality Assurance

- **Zero Data Fabrication**: Reports only contain authentic telemetry, CRS bounds, and model inferences persisted in the database.
- **Calibrated Scores**: Displayed conformal prediction scores represent true calibrated empirical accuracies.
- **Automated Test Coverage**: 129 backend automated tests passing with 100% success rate across Phases 1–9.
