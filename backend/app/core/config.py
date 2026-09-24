from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """SatQuery AI System Configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "SatQuery AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server & Networking
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Ingestion & Geospatial Safety
    MAX_UPLOAD_SIZE_MB: int = 500
    PREVIEW_MAX_SIZE: int = 2048

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./satquery.db",
        description="Async SQLAlchemy database connection string"
    )

    # Object Storage (MinIO / S3)
    STORAGE_BACKEND: str = "minio"  # 'minio' or 'local'
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "satquery_admin"
    MINIO_SECRET_KEY: str = "satquery_password_123"
    MINIO_BUCKET: str = "satquery-imagery"
    MINIO_SECURE: bool = False

    # Local storage fallback directory
    LOCAL_STORAGE_PATH: str = "./data/storage"

    # AI Runtime & Specialist Models (Phase 2)
    AI_DEVICE: str = "auto"  # 'auto', 'cpu', 'cuda'
    AI_USE_MOCK: bool = False  # Enable deterministic mock models for unit tests and offline testing
    AI_VQA_MODEL: str = "Salesforce/blip-vqa-base"
    AI_CAPTION_MODEL: str = "Gurveer05/blip-image-captioning-base-rscid-finetuned"
    AI_GROUNDING_MODEL: str = "google/owlvit-base-patch32"
    AI_IMAGE_SIZE: int = 384  # Standard input resolution for BLIP vision backbone


@lru_cache()
def get_settings() -> Settings:
    return Settings()
