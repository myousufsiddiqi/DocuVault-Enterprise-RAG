import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger("docuvault.database")

# 1. Asynchronous SQLAlchemy 2.0+ Engine
engine: AsyncEngine = create_async_engine(
    settings.async_database_url,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    echo=settings.DEBUG,
    future=True,
)

# 2. Asynchronous Session Factory
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# 3. Modern Declarative Base with Async Attribute Support
class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy ORM models in DocuVault AI."""
    pass


# 4. Dependency Injection Provider for FastAPI Routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields an asynchronous database session.
    Guarantees session closure and automated rollback in case of unhandled exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as exc:
            logger.error("Database transaction rolled back due to error: %s", exc, exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


# 5. Database Initialization & Extension Management
async def init_db_extensions() -> None:
    """
    Verifies database connectivity, enables pgvector, and creates all tables/indexes.
    Executed during application lifespan startup.
    """
    # Import models locally to guarantee they are registered with Base metadata
    from app.models.document import Document, DocumentChunk, DocumentExtraction  # noqa: F401

    logger.info("Initializing database connection and pgvector extension...")
    async with engine.begin() as conn:
        # 1. Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # 2. Automatically create tables and indexes (HNSW & GIN)
        logger.info("Ensuring all relational tables and vector indexes exist...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 3. Verify vector extension availability
        result = await conn.execute(
            text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")
        )
        row = result.fetchone()
        if row:
            logger.info("pgvector extension verified: %s (version %s)", row[0], row[1])
        else:
            logger.warning("pgvector extension was created but could not be queried.")


async def close_db_connection() -> None:
    """Disposes the async engine pool gracefully during application shutdown."""
    logger.info("Closing asynchronous database connection pool...")
    await engine.dispose()
    logger.info("Database connection pool disposed successfully.")
