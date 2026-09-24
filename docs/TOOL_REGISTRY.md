# SatQuery AI — Tool Registry & Specialist Interfaces

## 1. Registry Architecture
The `ToolRegistry` serves as the single source of truth for all analytical capabilities accessible to the SatQuery Agent.

```
                  ┌──────────────────────┐
                  │     ToolRegistry     │
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │  single_vqa  │ │single_caption│ │ PlannedTools │
     │ (Phase 2/3)  │ │ (Phase 2/3)  │ │ (Phase 4-6)  │
     └──────┬───────┘ └──────┬───────┘ └──────────────┘
            │                │
            ▼                ▼
     ┌───────────────────────────────┐
     │        AnalysisService        │
     └──────────────┬────────────────┘
                    │
                    ▼
     ┌───────────────────────────────┐
     │         AI Runtime            │
     └───────────────────────────────┘
```

---

## 2. Tool Interface Specification

Every analytical tool implements the `AnalysisTool` abstract base class:

```python
class AnalysisTool(ABC):
    name: str
    version: str
    task: str
    description: str
    status: str  # "available" or "planned"

    supported_input_types: List[str]
    supported_modalities: List[str]
    required_inputs: List[str]
    optional_parameters: Dict[str, Any]

    def validate_inputs(self, input_context: Dict[str, Any], parameters: Dict[str, Any]) -> None:
        ...

    def get_schema(self) -> Dict[str, Any]:
        ...

    async def execute(
        self,
        input_context: Dict[str, Any],
        parameters: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        ...

    def normalize_result(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        ...
```

---

## 3. Registered Tool Catalog

| Tool Name | Task | Status | Target Modalities | Inputs |
| :--- | :--- | :--- | :--- | :--- |
| `single_image_vqa` | `VISUAL_QUESTION_ANSWERING` | **Available** | Optical, Multispectral, SAR | `image_id`, `query` |
| `single_image_caption` | `SCENE_DESCRIPTION` | **Available** | Optical, Multispectral, SAR | `image_id` |
| `grounding` | `GROUNDING` | *Planned (Phase 4)* | Optical, Multispectral, SAR | `image_id`, `query` |
| `change_detection` | `CHANGE_ANALYSIS` | *Planned (Phase 5)* | Optical, Multispectral, SAR | `before_image_id`, `after_image_id` |
| `change_vqa` | `CHANGE_ANALYSIS` | *Planned (Phase 5)* | Optical, Multispectral, SAR | `before_image_id`, `after_image_id`, `query` |
| `optical_sar_analysis` | `CROSS_MODAL_ANALYSIS` | *Planned (Phase 6)* | Optical, SAR | `optical_image_id`, `sar_image_id`, `query` |

---

## 4. API Observability
Clients inspect the tool registry via:
```http
GET /api/v1/agent/tools
```
This enables both frontend capability discovery and automated auditing of executable versus planned tools.
