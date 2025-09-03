import datetime
import time
from functools import lru_cache

from app.config.loggers import app_logger as logger
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.secrets import inject_infisical_secrets


class Settings(BaseSettings):
    """Configuration settings for the application."""

    # Databases
    MONGO_DB: str
    REDIS_URL: str
    CHROMADB_HOST: str
    CHROMADB_PORT: int
    POSTGRES_URL: str
    RABBITMQ_URL: str

    # OAuth & Authentication
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    ENABLE_PUBSUB_JWT_VERIFICATION: bool = True
    GOOGLE_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"

    # Google
    GOOGLE_API_KEY: str

    # WorkOS Authentication
    WORKOS_API_KEY: str = ""
    WORKOS_CLIENT_ID: str = ""
    WORKOS_COOKIE_PASSWORD: str = ""

    # External API Keys
    BING_API_KEY: str
    ASSEMBLYAI_API_KEY: str
    DEEPGRAM_API_KEY: str
    OPENWEATHER_API_KEY: str
    RESEND_API_KEY: str
    RESEND_AUDIENCE_ID: str
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    COMPOSIO_KEY: str

    # Webhook Secrets
    COMPOSIO_WEBHOOK_SECRET: str

    # Blog Management
    BLOG_BEARER_TOKEN: str  # Bearer token for blog management operations

    # Service URL's
    LLM_URL: str = "https://llm.aryanranderiya1478.workers.dev/"
    BING_SEARCH_URL: str = "https://api.bing.microsoft.com/v7.0/search"

    # Environment & Deployment
    ENV: str = "production"
    HOST: str = "https://api.heygaia.io"
    FRONTEND_URL: str = "https://heygaia.io"
    DUMMY_IP: str = "8.8.8.8"
    DISABLE_PROFILING: bool = False
    WORKER_TYPE: str = "unknown"

    # Miscellaneous
    LLAMA_INDEX_KEY: str
    OPENAI_API_KEY: str
    GCP_TOPIC_NAME: str

    # Memory Configuration
    MEM0_API_KEY: str
    MEM0_ORG_ID: str
    MEM0_PROJECT_ID: str

    # Code Execution
    E2B_API_KEY: str

    # Dodo Payments Configuration
    DODO_PAYMENTS_API_KEY: str
    DODO_WEBHOOK_PAYMENTS_SECRET: str = ""

    # Analytics Configuration
    SENTRY_DSN: str = ""

    # Cerebras AI Configuration
    CEREBRAS_API_KEY: str

    @computed_field  # type: ignore
    @property
    def ENABLE_PROFILING(self) -> bool:
        """Enable profiling only if explicitly enabled in production."""
        return self.ENV == "production" and not self.DISABLE_PROFILING

    @computed_field  # type: ignore
    @property
    def GOOGLE_CALLBACK_URL(self) -> str:
        """Google OAuth callback URL."""
        return f"{self.HOST}/api/v1/oauth/google/callback"

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

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow",
    )

    MAX_REMINDER_DURATION: datetime.timedelta = datetime.timedelta(days=180)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.

    This function uses LRU cache to ensure settings are instantiated only once,
    avoiding expensive Pydantic validation on every import.
    """
    logger.info("Starting settings initialization...")

    infisical_start = time.time()
    inject_infisical_secrets()
    logger.info(f"Infisical secrets loaded in {(time.time() - infisical_start):.3f}s")

    return Settings()  # type: ignore
    # because we are initializing settings with environment variables


settings = get_settings()
