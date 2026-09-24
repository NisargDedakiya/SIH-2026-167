# Frontend UX Audit — SatQuery AI (Phase 9 Pre-Implementation Review)

## 1. Executive Summary

This UX audit assesses the current state of the SatQuery AI web application across Phases 1–8.
While each individual phase delivered functional interfaces (`/upload`, `/images/[id]`, `/temporal`, `/cross-modal`, `/evaluation`), the user experience currently presents as a disconnected collection of specialist developer tools rather than a unified, intuitive remote-sensing product.

---

## 2. Detailed Findings

### A. Navigation & Information Architecture
- **Fragmented Workspaces:** Users currently have to guess which page to use based on technical terms (`/temporal` for two images, `/cross-modal` for Optical+SAR, `/images/[id]` for single image). A non-technical user or jury member cannot simply upload data and ask a question.
- **Missing Core Views:**
  - No dedicated **History** view (`/history`) to review past queries without knowing the database ID.
  - No central **Reports Library** (`/reports`) to download analysis certificates.
  - No persistent **Analysis Detail** view (`/analysis/[id]`); results exist only in ephemeral client state and are lost on refresh.
  - No searchable **Image Catalog** (`/images`).
- **Header Navigation:** Contains inconsistent links (`Ingestion`, `Bi-Temporal`, `Optical + SAR`, `Evaluation`) instead of product-level navigation (`Dashboard`, `New Analysis`, `History`, `Images`, `Reports`, `Evaluation`).

### B. Input Inspection & Validation
- **Redundant Upload Logic:** `image-uploader.tsx` is mounted on `/` and `/upload` with duplicated dropzone handling.
- **Disconnected Compatibility Checks:** Compatibility between temporal pairs or optical-SAR pairs is only validated inside their isolated workspace components, not upfront during general input selection.
- **Technical Jargon in UI:** Input requirements frequently surface database terms (`pair_id`, `image_id`) rather than user-friendly badges (`T1 Before Image`, `T2 After Image`, `Optical Sentinel-2`, `SAR Sentinel-1`).

### C. Analysis Execution & Progress
- **Simulated Progress Timers:** `query-panel.tsx` uses client-side `setTimeout` timers to fake transition stages (`validating`, `classifying`, `planning`, `running`) rather than binding directly to observable backend trace events.
- **Hidden Observable Events:** The agent trace system records observable milestones, but they are tucked away inside collapsible raw JSON blocks rather than a clean step-by-step milestone checklist.

### D. Result Presentation & Aesthetics
- **Inconsistent Card Styles:** Result cards across VQA, Grounding, Temporal, and Cross-Modal use varying border colors, background opacities, and font sizes.
- **Unstructured Answers:** Answers are presented as raw strings without distinguishing **Direct Observations** from **Model Inferences** or **Uncertainty Disclaimers**.
- **Confidence Visualization:** Confidence is rendered as a plain text percentage without explaining the estimation method or highlighting when calibration is absent.
- **Model Attribution:** Model provenance (e.g. `satquery-rs-v1` with BigEarthNet LoRA adapter) is displayed inconsistently across tabs.

### E. Evidence Visualization
- **Separate Viewers:** `evidence-viewer.tsx` handles single-image grounding, `bitemporal-viewer.tsx` handles change split/diff, and `cross-modal-workspace.tsx` embeds its own viewer. There is no unified evidence viewer supporting cross-modal synchronized zooming or region inspection.
- **Accessibility & Interactivity:** Missing zoom/pan controls, fit-to-view shortcuts, and keyboard accessibility for bounding box selection.

### F. Reports & Exports
- **No Export Functionality:** Currently, there is zero report generation capability in the frontend or backend. Users cannot export findings to HTML, PDF, JSON, or downloadable zip packages for field or academic use.

### G. Error Handling & Mobile Responsiveness
- **Raw Error Disclosures:** API errors occasionally bubble up as unhandled alert boxes or raw `500 Internal Server Error` strings.
- **Mobile Overflows:** Large multi-column raster grids lack responsive wrapping on tablet and mobile viewports.

---

## 3. Actionable Remediation Plan (Phase 9 Targets)

| Issue | Remediation in Phase 9 |
| :--- | :--- |
| Fragmented workspaces | Create a unified **New Analysis Workspace** (`/analyze`) that automatically routes single-image, bi-temporal, and optical-SAR queries. |
| Ephemeral analysis state | Build stable route `/analysis/[id]` that reconstructs results, evidence, and traces directly from backend database. |
| Missing history & reports | Add dedicated `/history` and `/reports` views with search, filters, and downloads. |
| Inconsistent evidence viewers | Build `EvidenceViewerUnified` supporting single-image, bi-temporal swipe/diff, and optical-SAR side-by-side. |
| No export mechanisms | Build backend report engine exporting publication-grade PDF, interactive HTML, machine JSON, and full ZIP packages. |
| Unstructured answers | Implement `ObservationsPanel` separating Observed Facts, Inferred Hypotheses, and Uncertain Cues. |
| Fake progress indicators | Implement `AnalysisProgress` displaying real observable execution milestones. |
