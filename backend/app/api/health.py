from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.schemas.common import HealthResponse, ReadyResponse
from app.core.config import get_settings
from app.core.logging import logger
from app.database.session import engine
from app.storage.object_store import get_object_store

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Fast lightweight liveness probe endpoint.
    Indicates that the FastAPI application process is alive and receiving HTTP traffic.
    Does not falsely claim database or storage are connected without checking (use /ready for dependencies).
    """
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        database="not_checked",
        storage="not_checked"
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check(response: Response):
    """
    Deep readiness probe endpoint.
    Validates that database (connectivity and schema consistency), object storage,
    and AI model registries are accessible and ready to process multimodal satellite inference queries.
    """
    services = {}
    is_ready = True

    # 1. Probe Database Connectivity & Schema Consistency
    try:
        from app.database.session import check_db_schema_ready
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        schema_ok, schema_status = check_db_schema_ready()
        if schema_ok:
            services["database"] = "ready"
        else:
            services["database"] = schema_status
            is_ready = False
    except Exception as e:
        logger.warning(f"Readiness probe database check failed: {e}")
        services["database"] = "unreachable"
        is_ready = False

    # 2. Probe Object Storage Accessibility
    try:
        storage = get_object_store()
        services["storage"] = "ready"
    except Exception as e:
        logger.warning(f"Readiness probe object storage check failed: {e}")
        services["storage"] = "unavailable"
        is_ready = False

    # 3. Probe AI Model Registry
    try:
        from app.ai.runtime import get_model_runtime
        runtime = get_model_runtime()
        model_count = len(runtime.registry.list_models())
        if model_count > 0:
            services["models"] = f"ready ({model_count} registered)"
        else:
            services["models"] = "MODEL_REGISTRY_UNAVAILABLE"
            is_ready = False
    except Exception as e:
        logger.warning(f"Readiness probe model registry check failed: {e}")
        services["models"] = "MODEL_REGISTRY_UNAVAILABLE"
        is_ready = False

    # 4. Probe Hardware Accelerator (GPU vs CPU Fallback)
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            services["gpu"] = f"cuda_available ({dev_name})"
        else:
            services["gpu"] = "cpu_fallback"
    except Exception:
        services["gpu"] = "cpu_fallback"

    overall_status = "ready" if is_ready else "not_ready"
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(
        status=overall_status,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        services=services
    )
