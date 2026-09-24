# SatQuery AI — Execution Trace Specification

## 1. Overview
The **Execution Trace** provides an auditable, fine-grained chronological account of every state transition during an Agent run.

> **SIH Problem Compliance**:
> Only observable execution facts are logged. Hidden reasoning tokens, raw chain-of-thought, or system prompt configurations are strictly excluded.

---

## 2. Event Types & Lifecycle Flow

An end-to-end Agent run generates the following chronological events:

| Event Sequence | Event Type | Description |
| :---: | :--- | :--- |
| 1 | `QUERY_RECEIVED` | Records original query string length and input image count. |
| 2 | `INPUT_VALIDATED` | Verifies image existence in DB, sensor modality, and geospatial presence. |
| 3 | `TASK_CLASSIFIED` | Records detected intent, confidence score, and factual reasoning summary. |
| 4 | `CAPABILITY_CHECKED` | Verifies task availability in capability matrix against active phase. |
| 5 | `PLAN_GENERATED` | Records generated workflow steps and planned tool names. |
| 6 | `TOOL_SELECTED` | Dispatches execution to a registered specialist tool adapter. |
| 7 | `TOOL_EXECUTED` | Captures tool completion status, execution duration (ms), and output metadata. |
| 8 | `RESULT_NORMALIZED` | Normalizes answer string and calibrated confidence score. |
| 9 | `FINAL_RESPONSE_GENERATED` | Emits final response contract to the user. |

---

## 3. Database Schema

Traces are persisted in two relational tables:

### `agent_runs`
- `id`: UUID (Primary Key)
- `analysis_id`: UUID (Nullable foreign reference)
- `original_query`: Text
- `normalized_query`: Text
- `detected_task`: String
- `classification_confidence`: Float
- `selected_tools`: JSON
- `plan_json`: JSON
- `status`: String (`completed`, `unavailable`, `ambiguous`, `failed`)
- `answer`: Text
- `confidence_score`: Float
- `confidence_method`: String
- `started_at`: DateTime (UTC)
- `completed_at`: DateTime (UTC)
- `duration_ms`: Integer

### `agent_trace_events`
- `id`: UUID (Primary Key)
- `agent_run_id`: UUID (Foreign Key to `agent_runs.id`)
- `sequence`: Integer
- `event_type`: String
- `tool_name`: String (Nullable)
- `status`: String
- `parameters_json`: JSON
- `output_metadata_json`: JSON
- `duration_ms`: Integer
- `timestamp`: DateTime (UTC)
