from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings (Groq API)
    GROQ_API_KEY: str = Field(
        default="gsk_mock_key_for_dev_mode",
        description="Groq Cloud API key",
    )
    GROQ_MODEL_NAME: str = Field(
        default="llama-3.3-70b-versatile",
        description="Active LLM model name, never hardcoded in service code",
    )

    # Vector DB (ChromaDB)
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_db",
        description="Local directory path where ChromaDB collections are persisted",
    )

    # Relational DB & Auth (Supabase)
    SUPABASE_URL: str = Field(
        default="https://placeholder-project.supabase.co",
        description="Supabase project URL",
    )
    SUPABASE_KEY: str = Field(
        default="placeholder_anon_key",
        description="Supabase anonymous public key",
    )

    # Observability (Langfuse)
    LANGFUSE_SECRET_KEY: str = Field(
        default="",
        description="Langfuse secret key (tracing enabled if provided)",
    )
    LANGFUSE_PUBLIC_KEY: str = Field(
        default="",
        description="Langfuse public key",
    )
    LANGFUSE_HOST: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse server host URL",
    )

    # Server Runtime Config
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment: development, staging, production",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level",
    )
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="List of allowed CORS origins for Next.js frontend",
    )


# Singleton settings instance
settings = Settings()
