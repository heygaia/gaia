import os
import time

from app.config.loggers import app_logger as logger
from app.utils.exceptions import InfisicalConfigError

from infisical_sdk import InfisicalSDKClient
from dotenv import load_dotenv

load_dotenv()


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
        start_time = time.time()
        logger.info("Connecting to Infisical...")

        client = InfisicalSDKClient(
            host="https://app.infisical.com",
            cache_ttl=3600,
        )
        client.auth.universal_auth.login(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )
        logger.info(
            f"Infisical authentication completed in {time.time() - start_time:.3f}s"
        )

        secrets_start = time.time()
        secrets = client.secrets.list_secrets(
            # The unique identifier for your Infisical project
            project_id=INFISICAL_PROJECT_ID,
            # Environment name (e.g., "development", "production")
            environment_slug=ENV,
            # Root path for secrets in the project
            # nosec B322 - Bandit in pre-commit flags as unsafe.
            secret_path="/",
            # Resolves any referenced secrets (e.g., ${SECRET})
            expand_secret_references=True,
            view_secret_value=True,  # Returns decrypted secret values, not just keys
            recursive=False,  # Does not fetch secrets from nested paths
            include_imports=True,  # Includes secrets imported from other projects/paths
        )
        logger.info(f"Infisical secrets fetched in {time.time() - secrets_start:.3f}s")

        injection_start = time.time()

        # Inject secrets from Infisical into environment variables
        # !IMPORTANT: Local environment variables take precedence over Infisical secrets.
        # This allows overriding Infisical values with local .env files or manually set variables.
        # Only sets the secret if it's not already present in the environment.
        for secret in secrets.secrets:
            if os.environ.get(secret.secretKey) is None:
                os.environ[secret.secretKey] = secret.secretValue

        logger.info(
            f"Secrets injected into environment in {time.time() - injection_start:.3f}s"
        )

    except Exception as e:
        raise InfisicalConfigError(
            f"Failed to fetch secrets from Infisical: {e}"
        ) from e
