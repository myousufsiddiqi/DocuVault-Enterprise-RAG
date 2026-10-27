import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import engine, get_db, init_db_extensions, close_db_connection
from app.api.v1.router import api_v1_router

# Structured Logging Configuration
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("docuvault.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Asynchronous lifespan manager for FastAPI.
    Handles startup infrastructure checks and graceful connection teardown.
    """
    logger.info("Starting up %s (v%s)...", settings.PROJECT_NAME, settings.VERSION)
    try:
        await init_db_extensions()
        logger.info("Database and vector extension ready.")
    except Exception as exc:
        logger.critical("Fatal error connecting to database on startup: %s", exc, exc_info=True)
        # In production container startup, allow healthcheck to track DB recovery
    
    yield
    
    logger.info("Initiating application graceful shutdown...")
    await close_db_connection()


# FastAPI Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Document Intelligence & Hybrid RAG Workbench Backend",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 1. CORS Middleware (Zoneless Angular 22 Dashboard Integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time-Ms"],
)


# 2. Telemetry Middleware (Zero-blocking latency instrumentation)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
    return response


# 3. Mount API v1 Router (Track A Ingestion & Track B Hybrid RAG)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


# 4. Foundational Routes & Health Check
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """Root metadata endpoint verifying service status."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG else "disabled",
    }


@app.get(f"{settings.API_V1_STR}/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Deep healthcheck verifying database connectivity and pgvector readiness.
    Used by container orchestration and Angular dashboard telemetry.
    """
    db_status = "unavailable"
    pgvector_status = "inactive"
    pgvector_version = None

    try:
        # Check active connection
        await db.execute(text("SELECT 1;"))
        db_status = "connected"

        # Check pgvector extension status
        result = await db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        )
        vector_row = result.fetchone()
        if vector_row:
            pgvector_status = "active"
            pgvector_version = vector_row[0]
    except Exception as exc:
        logger.error("Health check database probe failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "database": db_status,
                "pgvector": pgvector_status,
                "error": str(exc),
            },
        )

    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "pgvector_extension": pgvector_status,
            "pgvector_version": pgvector_version,
        },
        "providers": {
            "mode": "100% Free Tier",
            "extraction_provider": settings.EXTRACTION_PROVIDER,
            "extraction_model": settings.GROQ_EXTRACTION_MODEL,
            "embedding_provider": settings.EMBEDDING_PROVIDER,
            "embedding_model": settings.EMBEDDING_MODEL,
            "embedding_dimensions": settings.EMBEDDING_DIM,
            "rerank_provider": settings.RERANK_PROVIDER,
            "rerank_model": settings.RERANK_MODEL,
        },
    }
