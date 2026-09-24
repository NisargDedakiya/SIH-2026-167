# SatQuery AI — SIH Live Demonstration Runbook

**Target Audience:** Smart India Hackathon (SIH 2026) Evaluation Committee / ISRO SAC Experts  
**Demonstration Time:** 3 – 5 Minutes  
**Demonstration Portal:** `http://localhost:3000/demo` (Demo Hub)  
**Backend Endpoint:** `http://localhost:8000/docs` (FastAPI Swagger)

---

## 1. Demo Objectives & Elevator Pitch (30 Seconds)

> *"Good morning, respected judges. We present SatQuery AI, an autonomous multimodal vision-language assistant built specifically for remote sensing. Unlike generic VLMs that hallucinate and treat satellite imagery like internet photographs, SatQuery AI preserves native geospatial coordinates, reasons across multi-spectral optical and radar SAR imagery, detects temporal changes, and provides mathematically verifiable evidence overlays with 1-click publication-grade reports."*

---

## 2. Canonical Demonstration Scenarios

### DEMO 1: Single-Image Remote-Sensing VQA (60 Seconds)
1. **Navigate to Demo Hub:** Click **Demo Hub** in the top navigation bar (`/demo`).
2. **Select Demo 1 Card:** "Demo 1: Single-Image Remote-Sensing VQA".
3. **Preset Query:** `"What type of land cover dominates this satellite image?"`
4. **Click "Run Demonstration":**
   - **Observe Live Execution Stepper:** Input raster validated -> Query interpreted -> Specialist VLM routed -> Inference executed.
   - **Highlight Findings:**
     - **Answer:** Accurate classification of terrain / land cover.
     - **Observations Breakdown:** Review `OBSERVED` (direct model features), `INFERRED` (land cover classification), and `UNCERTAIN` (resolution limits).
     - **Confidence Card:** Note the calibrated confidence score (e.g. 88%) with explicit methodological basis.
     - **Technical Trace:** Expand to show sub-second tool execution and timestamped event records.

---

### DEMO 2: Text-Guided Spatial Grounding (60 Seconds)
1. **Select Demo 2 Card:** "Demo 2: Text-Guided Spatial Grounding".
2. **Preset Query:** `"Highlight the buildings in this image."`
3. **Click "Run Demonstration":**
   - **Observe Intent Classification:** Agent interprets directive as `GROUNDING` (not generic VQA).
   - **Highlight Evidence Viewer:**
     - Inspect localized bounding boxes overlaid dynamically on the satellite raster.
     - Note both **pixel coordinates** $[x_1, y_1, x_2, y_2]$ and **native geospatial bounds** (UTM coordinates in EPSG:32643).
     - Zoom and pan across localized feature boundaries.

---

### DEMO 3: Bi-Temporal Change Detection (60 Seconds)
1. **Select Demo 3 Card:** "Demo 3: Bi-Temporal Change Detection".
2. **Preset Query:** `"What changed between these images?"`
3. **Click "Run Demonstration":**
   - **Observe Temporal Validation:** Agent verifies $T_1 < T_2$ and calculates spatial intersection.
   - **Highlight Change Difference Map:**
     - Inspect quantitative change metrics: surface change percentage (e.g. 14.8%) and isolated change polygon count.
     - Demonstrate difference map toggle between pre-event T1 and post-event T2 acquisitions.

---

### DEMO 4: Optical + SAR Multimodal Fusion (60 Seconds)
1. **Select Demo 4 Card:** "Demo 4: Optical + SAR Multimodal Fusion".
2. **Preset Query:** `"Compare optical and SAR imagery."`
3. **Click "Run Demonstration":**
   - **Observe Dual-Stream Processing:** Optical multispectral reflectance vs. SAR log-scale decibel backscatter.
   - **Highlight Joint vs. Modality-Specific Evidence:**
     - Point out all-weather structural backscatter revealed by SAR that optical imagery alone could not isolate.
     - Note explicit agreement / disagreement reporting.

---

## 3. Publication-Grade Multi-Format Export (30 Seconds)

1. On any completed analysis, point to the top action bar:
   - Click **Vector PDF**: Downloads formal two-column vector PDF compiled via ReportLab with executive summary, metadata tables, confidence card, and evidence crops.
   - Click **Interactive HTML**: Opens self-contained standalone HTML report viewable in any offline browser.
   - Click **JSON Schema**: Demonstrates machine-readable, schema-validated report for automated geospatial pipelines.
   - Click **ZIP Package**: Demonstrates self-contained deliverable package (`analysis.json`, `report.html`, `report.pdf`, `evidence/`, `trace.json`, `README.txt`).

---

## 4. Concluding Statement (15 Seconds)

> *"SatQuery AI provides an end-to-end, zero-fabrication remote sensing intelligence platform: from ingestion to agentic planning, multimodal fusion, spatial evidence, and verified reporting. Thank you, and we welcome your questions."*
