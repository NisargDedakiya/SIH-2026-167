# Phase 5: Bi-Temporal Change Intelligence Subsystem

Welcome to the **Bi-Temporal Change Intelligence Subsystem** documentation for SatQuery AI (ISRO Smart India Hackathon Problem Statement 26167).

## Architecture & Documents
- [Phase 5 Core Specification](../PHASE_5.md): End-to-end architecture, API reference, invariant guarantees, and database schema.
- [Change Detection Model Selection](change_detection_model_selection.md): Deep-dive research on Siamese architectures (FC-EF, FC-Siam-diff, FC-Siam-conc, BIT, ChangeFormer) and rationale for selecting feature differencing.
- [Agentic Router & Capability Resolver](../AGENT_ARCHITECTURE.md): Multi-image intent classification, dynamic tool resolution, and parameter compilation.

## Key Subsystems
1. **Validation & Compatibility**: `backend/app/temporal/compatibility.py` and `validator.py`.
2. **Non-Destructive Alignment**: `backend/app/temporal/alignment.py`.
3. **Change Detection Models**: `backend/app/ai/change_detection.py`.
4. **Change Map & Morphology**: `backend/app/temporal/change_map.py`.
5. **Region Extraction & Coordinate Mapping**: `backend/app/temporal/regions.py`.
6. **Change Description & Change VQA**: `backend/app/temporal/description.py` & `change_vqa.py`.
7. **Service Coordinator**: `backend/app/temporal/service.py`.
8. **Frontend Dual-Canvas Workspace**: `frontend/app/temporal/page.tsx` & `frontend/components/bitemporal-viewer.tsx`.
