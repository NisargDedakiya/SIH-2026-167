# Phase 6: Cross-Modal Visual Question Answering (VQA)

## 1. Task Definition
Cross-Modal VQA enables users to query co-registered Optical and SAR images simultaneously:
- *"Are the bright features in the SAR image buildings or surface roughness?"*
- *"Can you detect water extent obscured by cloud cover in the optical raster?"*
- *"Verify if the dark optical region is open water or shadowed terrain using SAR."*

---

## 2. Reasoning Flow
1. **Query Intent Recognition**: The `QueryClassifier` flags questions referencing optical and SAR terms (e.g., "SAR", "radar", "optical", "backscatter", "penetrate", "cloud").
2. **Specialist Tool Routing**: The `AgentRouter` routes execution to `optical_sar_vqa` specialist tool.
3. **Modality Evidence Generation**: The reasoning engine builds separate optical and SAR context paragraphs, evaluating cross-sensor consistency before synthesizing the final answer.
4. **Observable Answer Structure**: Answers provide unambiguous natural language findings, citing optical spectral evidence and SAR structural evidence.
