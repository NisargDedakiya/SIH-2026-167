# SatQuery AI — Agentic Query Router & Orchestration Architecture

## 1. Overview
SatQuery AI Phase 3 implements a **controlled agentic orchestrator** designed specifically for high-reliability remote-sensing intelligence (ISRO SIH Problem 26167).

Instead of an unconstrained autonomous agent generating arbitrary Python code or calling unrestricted APIs, SatQuery uses a deterministic, auditable pipeline:

```
                      USER QUERY + SATELLITE IMAGES
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │   Query Normalizer     │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │   Intent Classifier    │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │  Capability Resolver   │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │   Workflow Planner     │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │ Allowed Tool Registry  │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │   Tool Executor        │
                       │ (Sandboxed Parameters) │
                       └───────────┬────────────┘
                                   │
                                   ▼
                       ┌────────────────────────┐
                       │   Result Aggregator    │
                       └───────────┬────────────┘
                                   │
                   ┌───────────────┼───────────────┐
                   ▼               ▼               ▼
                 Answer        Confidence     Observable
                                                 Trace
```

---

## 2. Core Subsystems

### 2.1 Query Normalizer (`QueryNormalizer`)
Sanitizes extraneous whitespace, newline characters, and casing artifacts without mutating the semantic token semantics of the user's inquiry.

### 2.2 Intent Classifier (`QueryClassifier`)
Employs a 4-stage hybrid classification mechanism:
1. **Input Context Analysis**: Evaluates image count (single vs bi-temporal) and sensor modalities (optical vs SAR).
2. **Deterministic Rules & Triggers**:
   - `VISUAL_QUESTION_ANSWERING`: Specific interrogative patterns (`what type of`, `how many`, `is there`, `?`).
   - `SCENE_DESCRIPTION`: Synthesis directives (`describe`, `caption`, `overview`, `summary`).
   - `GROUNDING`: Spatial localization directives (`highlight`, `outline`, `bounding box`, `where is`).
   - `CHANGE_ANALYSIS`: Temporal comparison prompts (`what changed`, `difference between`, `two dates`).
   - `CROSS_MODAL_ANALYSIS`: Cross-sensor prompts (`optical and sar`, `combine sar`).
3. **Ambiguity Detection**: Flags underspecified queries (e.g., *"Tell me about this."*) and returns controlled clarifications rather than unguided model guesses.
4. **Observable Reasoning Summary**: Emits plain factual justifications (no private internal chain-of-thought).

### 2.3 Capability Resolver (`CapabilityResolver`)
Matches detected intent against the active capability matrix:
- **Phase 3 Executable**: `VISUAL_QUESTION_ANSWERING` (`single_image_vqa`) and `SCENE_DESCRIPTION` (`single_image_caption`).
- **Planned Capabilities**: `GROUNDING` (Phase 4), `CHANGE_ANALYSIS` (Phase 5), `CROSS_MODAL_ANALYSIS` (Phase 6).
- **Non-Fallback Invariant**: When an unavailable capability is identified, the system explicitly reports unavailability and logs the recognized intent. It **never** executes an incorrect fallback model.

### 2.4 Workflow Planner (`WorkflowPlanner`)
Validates input schemas and compiles strict, deterministic plan steps. Forbids arbitrary parameters from reaching specialist models.

### 2.5 Tool Executor (`ToolExecutor`)
Invokes pre-registered `AnalysisTool` adapters within a sandboxed environment. Completely isolates system calls, prohibiting any runtime `eval()`, `exec()`, shell access, or unsanctioned URL fetches.

### 2.6 Result Aggregator (`ResultAggregator`)
Normalizes answers, calculates calibrated confidence scores, and collates visual evidence into the standardized response contract.

### 2.7 Execution Trace (`ExecutionTrace`)
Instruments each stage with microsecond precision, capturing observable facts and state transitions persisted in `agent_runs` and `agent_trace_events`.

---

## 3. Security Boundaries
1. **No Code Execution**: Neither the user query nor model outputs can trigger dynamic code evaluation.
2. **Immutable Tool Registry**: Tools must be registered at runtime initialization. No dynamic tool creation.
3. **Strict Parameter Validation**: Every parameter passed to underlying models is validated against Pydantic definitions.
4. **Observable Facts Privacy**: Hidden prompts or intermediate model tokens are never logged or returned.
