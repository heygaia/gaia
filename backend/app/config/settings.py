import datetime
import os

from infisical_sdk import InfisicalSDKClient
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class InfisicalConfigError(Exception):
    """Exception raised for errors related to Infisical configuration."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def inject_infisical_secrets():
    INFISICAL_TOKEN = os.getenv("INFISICAL_TOKEN")
    INFISICAL_PROJECT_ID = os.getenv("INFISICAL_PROJECT_ID")
    ENV = os.getenv("ENV", "production")
    CLIENT_ID = os.getenv("INFISICAL_MACHINE_INDENTITY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("INFISICAL_MACHINE_INDENTITY_CLIENT_SECRET")

    if not INFISICAL_TOKEN:
        raise InfisicalConfigError(
            "INFISICAL_TOKEN is missing. This is required for secrets management."
        )
    elif not INFISICAL_PROJECT_ID:
        raise InfisicalConfigError(
            "INFISICAL_PROJECT_ID is missing. This is required for secrets management."
        )

    elif not CLIENT_ID:
        raise InfisicalConfigError(
            "INFISICAL_MACHINE_INDENTITY_CLIENT_ID is missing. This is required for secrets management."
        )

    elif not CLIENT_SECRET:
        raise InfisicalConfigError(
            "INFISICAL_MACHINE_INDENTITY_CLIENT_SECRET is missing. This is required for secrets management."
        )

    try:
        client = InfisicalSDKClient(host="https://app.infisical.com")
        client.auth.universal_auth.login(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        secrets = client.secrets.list_secrets(
            project_id=INFISICAL_PROJECT_ID,  # The unique identifier for your Infisical project
            environment_slug=ENV,  # Environment name (e.g., "development", "production")
            # Root path for secrets in the project
            secret_path="/",  # nosec B322 - Bandit in pre-commit flags as unsafe.
            expand_secret_references=True,  # Resolves any referenced secrets (e.g., ${SECRET})
            view_secret_value=True,  # Returns decrypted secret values, not just keys
            recursive=False,  # Does not fetch secrets from nested paths
            include_imports=True,  # Includes secrets imported from other projects/paths
        )
        for secret in secrets.secrets:
            os.environ[secret.secretKey] = secret.secretValue

    except Exception as e:
        raise InfisicalConfigError(
            f"Failed to fetch secrets from Infisical: {e}"
        ) from e


class Settings(BaseSettings):
    """Configuration settings for the application."""

    # Databases
    MONGO_DB: str
    REDIS_URL: str
    CHROMADB_HOST: str
    CHROMADB_PORT: int
    POSTGRES_URL: str

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
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

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

    # Celery Configuration
    RABBITMQ_URL: str

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

    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="allow",
    )

    MAX_REMINDER_DURATION: datetime.timedelta = datetime.timedelta(days=180)


inject_infisical_secrets()
settings = Settings()  # type: ignore
