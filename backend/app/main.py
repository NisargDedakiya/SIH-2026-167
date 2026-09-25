from contextlib import asynccontextmanager
import time
import uuid
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router, health_router
from app.core.config import get_settings
from app.core.logging import logger, request_id_ctx, setup_logging
from app.database.session import init_db

settings = get_settings()
setup_logging(settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Database schema and AI Runtime
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT})")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}. If in development, schema will create on first write.")
    try:
        from app.ai.runtime import get_model_runtime
        runtime = get_model_runtime()
        model_count = len(runtime.registry.list_models())
        if model_count == 0:
            logger.error("AI ModelRuntime startup warning: 0 specialist models registered.")
        else:
            logger.info(f"AI ModelRuntime ready with {model_count} registered models.")
    except Exception as e:
        logger.error(f"AI ModelRuntime startup failure: {e}", exc_info=True)
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="Agentic Vision-Language Assistant for Multimodal Remote Sensing Image Analysis (ISRO SIH Problem 26167)",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Configuration - avoid wildcard when credentials are enabled
allowed_origins = settings.cors_origin_list if settings.cors_origin_list else ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_and_timing_middleware(request: Request, call_next):
    """Assigns unique correlation ID, sets security headers, and logs execution duration for every request."""
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_ctx.set(req_id)
    start_time = time.time()

    response = await call_next(request)

    duration_ms = int((time.time() - start_time) * 1000)
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Log non-health requests
    if request.url.path != "/health":
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={
                "request_id": req_id,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "operation": f"{request.method} {request.url.path}"
            }
        )

    request_id_ctx.reset(token)
    return response


# Global Exception Handlers to mask internal server stack traces and emit standardized error schemas
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", str(uuid.uuid4()))
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code") or (
            "IMAGE_OBJECT_MISSING" if exc.status_code == 409
            else ("MODEL_UNAVAILABLE" if exc.status_code == 503
            else ("VALIDATION_ERROR" if exc.status_code in (400, 422)
            else ("RESOURCE_NOT_FOUND" if exc.status_code == 404
            else "HTTP_ERROR")))
        )
        msg = exc.detail.get("message") or exc.detail.get("detail") or "An HTTP error occurred."
        details = exc.detail.get("details", {})
        if "suggested_action" in exc.detail:
            details["suggested_action"] = exc.detail["suggested_action"]
    else:
        msg = str(exc.detail) if exc.detail else "An HTTP error occurred."
        detail_lower = msg.lower()
        if exc.status_code == 409 or "storage" in detail_lower or "missing" in detail_lower:
            code = "IMAGE_OBJECT_MISSING"
        elif exc.status_code == 503:
            code = "DATABASE_SCHEMA_MISMATCH" if ("database" in detail_lower or "schema" in detail_lower) else "MODEL_UNAVAILABLE"
        elif exc.status_code in (400, 422):
            code = "UNSUPPORTED_MODALITY" if "modality" in detail_lower else "VALIDATION_ERROR"
        elif exc.status_code == 404:
            code = "RESOURCE_NOT_FOUND"
        elif "align" in detail_lower:
            code = "ALIGNMENT_FAILURE"
        elif "modality" in detail_lower:
            code = "UNSUPPORTED_MODALITY"
        else:
            code = "HTTP_ERROR"
        details = {}

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": msg,
            "error": {
                "code": code,
                "message": msg,
                "details": details,
                "trace_id": req_id
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed.",
            "errors": exc.errors(),
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check the parameter specifications.",
                "details": {"validation_errors": exc.errors()},
                "trace_id": req_id
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = request_id_ctx.get() or request.headers.get("X-Request-ID", str(uuid.uuid4()))
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred while processing the request.",
            "request_id": req_id,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred during execution. Stack traces are masked.",
                "details": {},
                "trace_id": req_id
            }
        }
    )


# Attach Routers
app.include_router(health_router)
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
