from fastapi import APIRouter
from .health import router as health_router
from .images import router as images_router
from .analysis import router as analysis_router
from .agent import router as agent_router
from .temporal import router as temporal_router
from .cross_modal import router as cross_modal_router
from .evaluation import router as evaluation_router
from .reports import router as reports_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(images_router, prefix="/images", tags=["Images"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(agent_router, prefix="/agent", tags=["Agent"])
api_router.include_router(temporal_router, prefix="/temporal", tags=["Temporal"])
api_router.include_router(cross_modal_router, prefix="/cross-modal", tags=["CrossModal"])
api_router.include_router(evaluation_router, prefix="/evaluation", tags=["Evaluation"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])

__all__ = [
    "api_router",
    "health_router",
    "analysis_router",
    "agent_router",
    "temporal_router",
    "cross_modal_router",
    "evaluation_router",
    "reports_router",
]


