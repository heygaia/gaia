import os
import time
from functools import lru_cache
from typing import Literal, Optional

from app.config.loggers import app_logger as logger
from app.config.secrets import inject_infisical_secrets
from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class BaseAppSettings(BaseSettings):
    """Base configuration settings for the application."""

    ENV: Literal["production", "development"] = "production"
    model_config = SettingsConfigDict(extra="allow")


class CommonSettings(BaseAppSettings):
    """Common settings required for all environments."""

    # ----------------------------------------------
    # Database Connections
    # ----------------------------------------------
    MONGO_DB: str
    REDIS_URL: str

    # ----------------------------------------------
    # Authentication & OAuth
    # ----------------------------------------------
    WORKOS_API_KEY: str
    WORKOS_CLIENT_ID: str
    WORKOS_COOKIE_PASSWORD: str

    # ----------------------------------------------
    # Environment & Deployment
    # ----------------------------------------------
    HOST: str = "https://api.heygaia.io"
    FRONTEND_URL: str = "https://heygaia.io"
    DUMMY_IP: str = "8.8.8.8"
    DISABLE_PROFILING: bool = False
    WORKER_TYPE: str = "unknown"

    # ----------------------------------------------
    # Computed Properties
    # ----------------------------------------------
    @computed_field  # type: ignore
    @property
    def ENABLE_PROFILING(self) -> bool:
        """Enable profiling only if explicitly enabled in production."""
        return self.ENV == "production" and not self.DISABLE_PROFILING

    # OAuth Callback URLs
    @computed_field  # type: ignore
    @property
    def WORKOS_REDIRECT_URI(self) -> str:
        """WorkOS OAuth callback URL."""
        return f"{self.HOST}/api/v1/oauth/workos/callback"

    @computed_field  # type: ignore
    @property
    def COMPOSIO_REDIRECT_URI(self) -> str:
        """Composio OAuth callback URL."""
        return f"{self.HOST}/api/v1/oauth/composio/callback"

    @computed_field  # type: ignore
    @property
    def GOOGLE_CALLBACK_URL(self) -> str:
        """Google OAuth callback URL."""
        return f"{self.HOST}/api/v1/oauth/google/callback"


class ProductionSettings(CommonSettings):
    """Strict settings required for production environment."""

    # ----------------------------------------------
    # Database & Message Queue Connections
    # ----------------------------------------------
    CHROMADB_HOST: str
    CHROMADB_PORT: int
    POSTGRES_URL: str
    RABBITMQ_URL: str

    # ----------------------------------------------
    # Authentication & OAuth
    # ----------------------------------------------
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"

    # ----------------------------------------------
    # External API Integration Keys
    # ----------------------------------------------
    BING_API_KEY: str
    LLAMA_INDEX_KEY: str

    # AI & Machine Learning
    OPENAI_API_KEY: str
    CEREBRAS_API_KEY: str
    GOOGLE_API_KEY: str

    # Media & Content Processing
    ASSEMBLYAI_API_KEY: str
    DEEPGRAM_API_KEY: str

    # Weather Services
    OPENWEATHER_API_KEY: str

    # Email & Communication
    RESEND_API_KEY: str
    RESEND_AUDIENCE_ID: str

    # Media Storage
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # External Service Integration
    COMPOSIO_KEY: str

    # ----------------------------------------------
    # Webhook Secrets & Security
    # ----------------------------------------------
    COMPOSIO_WEBHOOK_SECRET: str
    DODO_WEBHOOK_PAYMENTS_SECRET: str = ""

    # ----------------------------------------------
    # Content Management
    # ----------------------------------------------
    BLOG_BEARER_TOKEN: str  # Bearer token for blog management operations

    # ----------------------------------------------
    # Memory & Storage Configuration
    # ----------------------------------------------
    MEM0_API_KEY: str
    MEM0_ORG_ID: str
    MEM0_PROJECT_ID: str

    # ----------------------------------------------
    # Code Execution Environment
    # ----------------------------------------------
    E2B_API_KEY: str

    # ----------------------------------------------
    # Payment Processing
    # ----------------------------------------------
    DODO_PAYMENTS_API_KEY: str

    # ----------------------------------------------
    # Monitoring & Analytics
    # ----------------------------------------------
    SENTRY_DSN: str = ""

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow",
    )


class DevelopmentSettings(CommonSettings):
    """Looser settings for development environment with defaults."""

    # ----------------------------------------------
    # Database & Message Queue Connections
    # ----------------------------------------------
    CHROMADB_HOST: Optional[str] = None
    CHROMADB_PORT: Optional[int] = None
    POSTGRES_URL: Optional[str] = None
    RABBITMQ_URL: Optional[str] = None

    # ----------------------------------------------
    # Authentication & OAuth
    # ----------------------------------------------
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    ENABLE_PUBSUB_JWT_VERIFICATION: bool = False
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"

    # ----------------------------------------------
    # External API Integration Keys
    # ----------------------------------------------
    # Search & Data Services
    BING_API_KEY: Optional[str] = None
    LLAMA_INDEX_KEY: Optional[str] = None

    # AI & Machine Learning
    OPENAI_API_KEY: Optional[str] = None
    CEREBRAS_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GCP_TOPIC_NAME: Optional[str] = None

    # Media & Content Processing
    ASSEMBLYAI_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None

    # Weather Services
    OPENWEATHER_API_KEY: Optional[str] = None

    # Email & Communication
    RESEND_API_KEY: Optional[str] = None
    RESEND_AUDIENCE_ID: Optional[str] = None

    # Media Storage
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    # External Service Integration
    COMPOSIO_KEY: Optional[str] = None

    # ----------------------------------------------
    # Webhook Secrets & Security
    # ----------------------------------------------
    COMPOSIO_WEBHOOK_SECRET: Optional[str] = None
    DODO_WEBHOOK_PAYMENTS_SECRET: Optional[str] = None

    # ----------------------------------------------
    # Content Management
    # ----------------------------------------------
    BLOG_BEARER_TOKEN: Optional[str] = (
        None  # Bearer token for blog management operations
    )

    # ----------------------------------------------
    # Memory & Storage Configuration
    # ----------------------------------------------
    MEM0_API_KEY: Optional[str] = None
    MEM0_ORG_ID: Optional[str] = None
    MEM0_PROJECT_ID: Optional[str] = None

    # ----------------------------------------------
    # Code Execution Environment
    # ----------------------------------------------
    E2B_API_KEY: Optional[str] = None

    # ----------------------------------------------
    # Payment Processing
    # ----------------------------------------------
    DODO_PAYMENTS_API_KEY: Optional[str] = None

    # ----------------------------------------------
    # Monitoring & Analytics
    # ----------------------------------------------
    SENTRY_DSN: Optional[str] = None

    # ----------------------------------------------
    # Environment Configuration
    # ----------------------------------------------
    ENV: Literal["production", "development"] = "development"

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow",
    )


@lru_cache(maxsize=1)
def get_settings():
    """
    Get cached settings instance based on environment.

    This function uses LRU cache to ensure settings are instantiated only once,
    avoiding expensive Pydantic validation on every import.
    """
    logger.info("Starting settings initialization...")

    infisical_start = time.time()
    inject_infisical_secrets()
    logger.info(f"Infisical secrets loaded in {(time.time() - infisical_start):.3f}s")

    env = os.getenv("ENV", "production")

    if env == "development":
        return DevelopmentSettings()  # type: ignore

    return ProductionSettings()  # type: ignore
    # type ignore because we are initializing settings with environment variables


settings = get_settings()
