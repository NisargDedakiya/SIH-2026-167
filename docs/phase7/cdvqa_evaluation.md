# Phase 7: CDVQA (Change Detection VQA) Evaluation & Temporal Pathway

## 1. Context & Architectural Separation
Change Detection Visual Question Answering (CDVQA) addresses bi-temporal pairs ($T_1, T_2$) to answer queries about what changed between epochs:
- *"Did urban residential structures increase between 2018 and 2022?"*
- *"Are there new road corridors or transport alterations?"*
- *"Was there deforestation or vegetation loss in this sector?"*

In SatQuery AI, bi-temporal change reasoning was implemented in **Phase 5** via `BiTemporalChangeVQATool`, `ChangeDetectionModel`, and spatial difference mapping.

---

## 2. Evaluation of Existing Phase 5 Change VQA
We evaluated the existing Change VQA system against change-type categories:
1. **Urban Expansion Queries**: Correctly leverages Siamese difference maps to determine whether structural changes match building geometries.
2. **Vegetation Depletion Queries**: Correlates negative difference clusters with historical vegetation masks.
3. **Infrastructure Alterations**: Correctly identifies linear corridor alterations.

---

## 3. Relationship to Single-Image Remote-Sensing Adaptation
1. **Feature Quality Uplift**:
   The single-image domain adaptation performed in Phase 7 (`satquery-rs-v1`) provides improved land-cover token semantics (CORINE classes: arable land, urban fabric, broad-leaved forest). When applied to extract feature representations at epoch $T_1$ and epoch $T_2$, the adapted vision encoder provides sharper class-boundary distinctions compared to a generic web VLM.
2. **Explicit Non-Interference**:
   In strict compliance with Part 21 of the Phase 7 specifications, we do NOT force the single-image VLM to absorb bi-temporal change weights. Phase 5's dedicated change detection architecture remains an independent modular specialist, avoiding catastrophic forgetting of change detection mechanics.
3. **Future Pathway (Phase 8/SIH)**:
   In Phase 8 (Benchmark & Evaluation Engine), CDVQA will be evaluated as a formal multi-temporal benchmark alongside VRSBench and RSVQA.
