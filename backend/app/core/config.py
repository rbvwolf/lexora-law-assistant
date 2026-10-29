from typing import List, Optional
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

    # Vector DB & Embeddings (ChromaDB)
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_db",
        description="Local directory path where ChromaDB collections are persisted",
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="intfloat/multilingual-e5-base",
        description="Embedding model name used for law articles and RAG retrieval",
    )

    # Document templates (.docx files named <template_id>.docx)
    TEMPLATES_DIR: str = Field(
        default="../data/templates",
        description="Directory holding .docx document templates (relative to the working directory)",
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

    def format_passage(self, text: str) -> str:
        """Format a document passage for embedding. multilingual-e5 requires 'passage: ' prefix."""
        if "e5" in self.EMBEDDING_MODEL_NAME.lower():
            return f"passage: {text}"
        return text

    def format_query(self, query: str) -> str:
        """Format a search query for embedding. multilingual-e5 requires 'query: ' prefix."""
        if "e5" in self.EMBEDDING_MODEL_NAME.lower():
            return f"query: {query}"
        return query


# Singleton settings instance
settings = Settings()


def format_passage(text: str, model_name: Optional[str] = None) -> str:
    """Helper to prefix 'passage: ' if active model is multilingual-e5."""
    active = model_name or settings.EMBEDDING_MODEL_NAME
    if "e5" in active.lower():
        return f"passage: {text}"
    return text


def format_query(query: str, model_name: Optional[str] = None) -> str:
    """Helper to prefix 'query: ' if active model is multilingual-e5."""
    active = model_name or settings.EMBEDDING_MODEL_NAME
    if "e5" in active.lower():
        return f"query: {query}"
    return query
