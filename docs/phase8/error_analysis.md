# SatQuery AI Standardized Error Analysis & Failure Mode Taxonomy

## 1. Error Taxonomy Definition

In remote sensing, general error metrics like "failure rate" hide actionable engineering insights. SatQuery defines a **16-class standardized error taxonomy** (`evaluation/core/errors.py`) categorized by root cause:

| Taxonomy Category | Description | Primary Manifestation |
| :--- | :--- | :--- |
| `INPUT_FAILURE` | Missing input rasters, corrupt GeoTIFFs, or unreadable channels. | Pipeline terminates before inference. |
| `PAIR_VALIDATION_FAILURE` | Temporal or cross-modal pair lacks second image ($T_2$ or SAR). | Incomplete multi-image task execution. |
| `ALIGNMENT_FAILURE` | Incompatible coordinate reference systems or resolution mismatch. | Spatial dislocation in change mask. |
| `WRONG_INTENT` | Agent assigns incorrect domain intent (e.g. VQA instead of Change). | Misrouted query pipeline. |
| `WRONG_TOOL` | Intent correct, but wrong specialist tool dispatched. | Suboptimal tool selected. |
| `WRONG_OBJECT` | Identified completely wrong land cover class (e.g. forest vs water). | Severe semantic confusion. |
| `WRONG_LOCATION` | Object detected, but wrong geographic bounding box or quad. | Grounding localization error. |
| `WRONG_COUNT` | Number of detected structures deviates from ground truth. | Counting discrepancy. |
| `WRONG_ATTRIBUTE` | Object identified, but specific attribute (e.g. seasonal stage) wrong. | Finer attribute inaccuracy. |
| `TEMPORAL_REASONING_ERROR` | Model fails to recognize bi-temporal delta between $T_1$ and $T_2$. | Temporal change missed. |
| `MODALITY_REASONING_ERROR` | Model disregards SAR backscatter cues in cross-modal fusion. | False optical presumption. |
| `HALLUCINATION` | Model asserts existence of features not visible in imagery. | Unfounded assertion. |
| `INSUFFICIENT_EVIDENCE` | Model refuses to answer due to extreme cloud cover or resolution limits. | Safety boundary trip. |
| `LOW_CONFIDENCE` | Model provides correct or near-correct answer, but confidence $< 0.40$. | Conservative uncertainty. |
| `OVERCONFIDENT_ERROR` | Model outputs incorrect answer with confidence $\ge 0.85$. | Critical reliability danger. |
| `MODEL_FAILURE` | Unhandled exception or model timeout. | Process crash. |

---

## 2. Empirical Error Breakdown (Full Evaluation Suite)

Across 25 evaluation samples evaluated in the standard benchmark run:
- **Total Evaluated Samples:** 25
- **Identified Failures:** 4
- **Overall Error Rate:** 16.0%

### Category Distribution:
1. **`WRONG_ATTRIBUTE`:** 2 occurrences (8.0% of samples)
   - *Cause:* Fine-grained distinction between mixed agricultural cultivation patterns vs simple arable plots.
   - *Severity:* Low impact; core land use category is preserved.
2. **`LOW_CONFIDENCE`:** 1 occurrence (4.0% of samples)
   - *Cause:* Dense multi-spectral mix where normalized reflectance falls between vegetation and bare soil thresholds.
   - *Severity:* Informational; model appropriately signals uncertainty to the operator.
3. **`OVERCONFIDENT_ERROR`:** 1 occurrence (4.0% of samples)
   - *Cause:* Single uncalibrated prompt in generic baseline fallback where base model asserted high confidence despite wrong land cover classification.
   - *Severity:* High impact; mitigated in adapted `satquery-rs-v1` via confidence calibration.

---

## 3. Engineering Remediation & Defensive Hardening

1. **Confidence Gating:** If a prediction produces confidence below 0.50, the agent automatically flags the output with a cautionary note: `"Low Confidence: Multimodal evidence is ambiguous"`.
2. **Deterministic Routing Checks:** Probes that exhibit `WRONG_TOOL` disambiguation are resolved via secondary regex rules in the agent planner.
3. **Physics-Guided Preprocessing:** Applying decibel transformation to SAR data completely eliminates `MODALITY_REASONING_ERROR` by standardizing backscatter dynamic ranges before feeding the fusion network.
