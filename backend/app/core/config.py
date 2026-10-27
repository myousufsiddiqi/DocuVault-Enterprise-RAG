from typing import List, Union
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    PROJECT_NAME: str = "DocuVault AI: Enterprise Document Intelligence & Hybrid RAG Workbench"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # CORS Whitelist (accepts string or list)
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:4200", "http://127.0.0.1:4200"]

    @property
    def cors_origin_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS

    # PostgreSQL & pgvector Credentials
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_secure_password"
    POSTGRES_DB: str = "docuvault"

    # Async Database Connection Pool Configuration
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_PRE_PING: bool = True

    @computed_field  # type: ignore[misc]
    @property
    def async_database_url(self) -> str:
        """Constructs the asynchronous asyncpg connection URL for SQLAlchemy."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- 100% FREE AI ARCHITECTURE CONFIGURATION ---

    # Track A: LLM Structured Extraction (100% Free Groq Cloud Tier)
    EXTRACTION_PROVIDER: str = "groq"
    GROQ_API_KEY: str = ""  # Populated from .env (User will provide this key)
    GROQ_EXTRACTION_MODEL: str = "llama-3.3-70b-versatile"

    # Track B: Vector Embeddings (100% Free Local FastEmbed - Zero API Keys, Zero Cost)
    EMBEDDING_PROVIDER: str = "fastembed"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384  # Fast, lightweight 384-dimensional dense vectors

    # Track B: Cross-Encoder Reranker (100% Free Local FlashRank - Zero API Keys, Zero Cost)
    RERANK_PROVIDER: str = "flashrank"
    RERANK_MODEL: str = "ms-marco-MiniLM-L-12-v2"

    # Optional Fallbacks / Cloud Keys (Inactive unless populated)
    OPENAI_API_KEY: str = ""
    OPENAI_EXTRACTION_MODEL: str = "gpt-4o-mini"
    COHERE_API_KEY: str = ""
    COHERE_RERANK_MODEL: str = "rerank-english-v3.0"


settings = Settings()
