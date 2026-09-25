from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings
from app.core.logging import logger
from .models import Base

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Global state tracking database schema readiness
db_schema_state = {"status": "uninitialized", "error": None}


async def init_db() -> None:
    """
    Initialize database schema, apply column migrations, and verify schema consistency.
    Guarantees that existing PostgreSQL or SQLite databases have all required columns
    without data deletion.
    """
    global db_schema_state
    try:
        async with engine.begin() as conn:
            # 1. Create any missing tables defined in Base
            await conn.run_sync(Base.metadata.create_all)

            dialect = engine.url.get_dialect().name

            # 2. Inspect existing columns and apply migrations for 'images' table
            if dialect == "postgresql":
                # PostgreSQL 9.6+ supports ADD COLUMN IF NOT EXISTS natively
                postgres_image_migrations = [
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS preview_key VARCHAR(512)",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS epsg_code INTEGER",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS resolution_x DOUBLE PRECISION",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS resolution_y DOUBLE PRECISION",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS bounds JSON",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS transform JSON",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS acquisition_time TIMESTAMP WITH TIME ZONE",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS sensor VARCHAR(128)",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS modality VARCHAR(64) DEFAULT 'unknown' NOT NULL",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS is_geospatial BOOLEAN DEFAULT FALSE NOT NULL",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS validation_status VARCHAR(32) DEFAULT 'valid' NOT NULL",
                    "ALTER TABLE images ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL",
                ]
                for stmt in postgres_image_migrations:
                    try:
                        await conn.execute(text(stmt))
                    except Exception as col_err:
                        logger.debug(f"Postgres column check notice: {col_err}")

                # Ensure analysis_jobs has pair_id and cross_modal_pair_id
                postgres_job_migrations = [
                    "ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS pair_id UUID REFERENCES bi_temporal_pairs(id) ON DELETE SET NULL",
                    "ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS cross_modal_pair_id UUID REFERENCES optical_sar_pairs(id) ON DELETE SET NULL",
                ]
                for stmt in postgres_job_migrations:
                    try:
                        await conn.execute(text(stmt))
                    except Exception as job_err:
                        logger.debug(f"Postgres job column check notice: {job_err}")

            elif dialect == "sqlite":
                # Inspect SQLite columns dynamically via PRAGMA
                res = await conn.execute(text("PRAGMA table_info(images)"))
                existing_cols = {row[1] for row in res.fetchall()}

                sqlite_image_migrations = [
                    ("preview_key", "VARCHAR(512)"),
                    ("epsg_code", "INTEGER"),
                    ("resolution_x", "FLOAT"),
                    ("resolution_y", "FLOAT"),
                    ("bounds", "JSON"),
                    ("transform", "JSON"),
                    ("acquisition_time", "DATETIME"),
                    ("sensor", "VARCHAR(128)"),
                    ("modality", "VARCHAR(64) DEFAULT 'unknown'"),
                    ("is_geospatial", "BOOLEAN DEFAULT 0"),
                    ("validation_status", "VARCHAR(32) DEFAULT 'valid'"),
                    ("updated_at", "DATETIME"),
                ]
                for col_name, col_type in sqlite_image_migrations:
                    if col_name not in existing_cols:
                        try:
                            await conn.execute(text(f"ALTER TABLE images ADD COLUMN {col_name} {col_type}"))
                            logger.info(f"Added missing column '{col_name}' to SQLite images table.")
                        except Exception as e:
                            logger.debug(f"Notice adding column {col_name}: {e}")

                res_jobs = await conn.execute(text("PRAGMA table_info(analysis_jobs)"))
                existing_job_cols = {row[1] for row in res_jobs.fetchall()}

                if "pair_id" not in existing_job_cols:
                    try:
                        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN pair_id CHAR(32) REFERENCES bi_temporal_pairs(id)"))
                    except Exception:
                        pass
                if "cross_modal_pair_id" not in existing_job_cols:
                    try:
                        await conn.execute(text("ALTER TABLE analysis_jobs ADD COLUMN cross_modal_pair_id CHAR(32) REFERENCES optical_sar_pairs(id)"))
                    except Exception:
                        pass

            # 3. Perform smoke query to verify schema alignment
            smoke_stmt = text(
                "SELECT id, original_filename, acquisition_time, sensor, modality, is_geospatial, validation_status "
                "FROM images LIMIT 1"
            )
            await conn.execute(smoke_stmt)

        db_schema_state["status"] = "ready"
        db_schema_state["error"] = None
        logger.info("Database schema initialized and verified successfully.")
    except Exception as e:
        db_schema_state["status"] = "DATABASE_SCHEMA_MISMATCH"
        db_schema_state["error"] = str(e)
        logger.error(f"Error initializing or verifying database schema: {e}", exc_info=True)
        raise


def check_db_schema_ready() -> tuple[bool, str]:
    """
    Returns (is_ready, status_code_or_message).
    Used by /ready probe to detect schema drift or incompatibility before user queries fail.
    """
    status = db_schema_state.get("status", "uninitialized")
    if status == "ready":
        return True, "ready"
    return False, status


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for obtaining an asynchronous database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
