from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Generic, Optional, Set, TypeVar

from app.config.loggers import app_logger as logger
from app.config.settings import settings
from app.utils.exceptions import ConfigurationError

T = TypeVar("T")


class MissingKeyStrategy(Enum):
    """Strategy for handling missing keys"""

    ERROR = "error"  # Raise exception immediately
    WARN = "warn"  # Log warning and return None
    WARN_ONCE = "warn_once"  # Log warning once per key and return None
    SILENT = "silent"  # Return None silently


class LazyLoader(Generic[T]):
    """
    Lazy loader that defers provider initialization until first access.

    Features:
    - Thread-safe singleton pattern per loader
    - Configurable error handling for missing keys
    - Validation caching to avoid repeated checks
    - Flexible warning system
    - Type safety with generics
    """

    def __init__(
        self,
        loader_func: Callable[[], T],
        required_keys: Optional[Set[str]] = None,
        strategy: MissingKeyStrategy = MissingKeyStrategy.ERROR,
        warning_message: Optional[str] = None,
        provider_name: Optional[str] = None,
        validate_keys_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ):
        """
        Initialize lazy loader.

        Args:
            loader_func: Function that creates the provider instance
            required_keys: Set of settings attribute names required
            strategy: How to handle missing keys
            warning_message: Custom warning message
            provider_name: Name for logging/error messages
            validate_keys_func: Custom validation function for the keys
        """
        self.loader_func = loader_func
        self.required_keys = required_keys or set()
        self.strategy = strategy
        self.warning_message = warning_message
        self.provider_name = provider_name or loader_func.__name__
        self.validate_keys_func = validate_keys_func

        self._instance: Optional[T] = None
        self._initialization_attempted = False
        self._lock = Lock()
        self._warned_keys: Set[str] = set()  # Track warned keys for WARN_ONCE

    def __call__(self) -> Optional[T]:
        """Get the provider instance, initializing if needed."""
        if self._instance is not None:
            return self._instance

        if self._initialization_attempted and self.strategy != MissingKeyStrategy.ERROR:
            return None

        with self._lock:
            # Double-check locking pattern
            if self._instance is not None:
                return self._instance

            if (
                self._initialization_attempted
                and self.strategy != MissingKeyStrategy.ERROR
            ):
                return None

            return self._initialize()

    def _initialize(self) -> Optional[T]:
        """Initialize the provider instance."""
        self._initialization_attempted = True

        # Check if required keys are present
        missing_keys = self._check_required_keys()
        if missing_keys:
            return self._handle_missing_keys(missing_keys)

        # Validate keys if custom validator provided
        if self.validate_keys_func:
            key_values = {}
            for key in self.required_keys:
                try:
                    key_values[key] = getattr(settings, key)
                except AttributeError:
                    key_values[key] = None

            if not self.validate_keys_func(key_values):
                return self._handle_validation_failure()

        try:
            # Initialize the provider
            self._instance = self.loader_func()
            logger.info(f"Successfully initialized provider: {self.provider_name}")
            return self._instance

        except Exception as e:
            error_msg = (
                f"Failed to initialize provider '{self.provider_name}': {str(e)}"
            )
            logger.error(error_msg)

            if self.strategy == MissingKeyStrategy.ERROR:
                raise ConfigurationError(error_msg) from e
            else:
                self._log_warning(f"Provider initialization failed: {str(e)}")
                return None

    def _check_required_keys(self) -> Set[str]:
        """Check which required keys are missing from settings."""
        missing_keys = set()
        for key in self.required_keys:
            try:
                value = getattr(settings, key)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    missing_keys.add(key)
            except AttributeError:
                missing_keys.add(key)
        return missing_keys

    def _handle_missing_keys(self, missing_keys: Set[str]) -> Optional[T]:
        """Handle missing keys according to strategy."""
        keys_str = ", ".join(missing_keys)

        if self.strategy == MissingKeyStrategy.ERROR:
            raise ConfigurationError(
                f"Missing required environment variables for '{self.provider_name}': {keys_str}"
            )

        # For non-error strategies, log warnings
        message = (
            self.warning_message or f"Missing keys for {self.provider_name}: {keys_str}"
        )

        if self.strategy == MissingKeyStrategy.WARN:
            self._log_warning(message)
        elif self.strategy == MissingKeyStrategy.WARN_ONCE:
            new_keys = missing_keys - self._warned_keys
            if new_keys:
                self._log_warning(f"{message} (first time warning)")
                self._warned_keys.update(new_keys)

        return None

    def _handle_validation_failure(self) -> Optional[T]:
        """Handle custom validation failure."""
        message = f"Key validation failed for provider '{self.provider_name}'"

        if self.strategy == MissingKeyStrategy.ERROR:
            raise ConfigurationError(message)
        else:
            self._log_warning(message)
            return None

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"[LazyLoader] {message}")

    def is_available(self) -> bool:
        """Check if the provider is available without initializing it."""
        missing_keys = self._check_required_keys()
        return len(missing_keys) == 0

    def force_initialize(self) -> T:
        """Force initialization and raise error if it fails."""
        original_strategy = self.strategy
        self.strategy = MissingKeyStrategy.ERROR
        try:
            result = self()
            if result is None:
                raise ConfigurationError(
                    f"Failed to initialize provider '{self.provider_name}'"
                )
            return result
        finally:
            self.strategy = original_strategy

    def reset(self):
        """Reset the loader (useful for testing)."""
        with self._lock:
            self._instance = None
            self._initialization_attempted = False
            self._warned_keys.clear()


class ProviderRegistry:
    """
    Registry for managing multiple lazy-loaded providers.
    Provides a centralized way to configure and access providers.
    """

    def __init__(self):
        self._providers: Dict[str, LazyLoader] = {}
        self._lock = Lock()

    def register(
        self,
        name: str,
        loader_func: Callable[[], T],
        required_keys: Optional[Set[str]] = None,
        strategy: MissingKeyStrategy = MissingKeyStrategy.WARN,
        warning_message: Optional[str] = None,
        validate_keys_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> LazyLoader[T]:
        """Register a new provider."""
        with self._lock:
            if name in self._providers:
                logger.warning(f"Provider '{name}' is being re-registered")

            provider = LazyLoader(
                loader_func=loader_func,
                required_keys=required_keys,
                strategy=strategy,
                warning_message=warning_message,
                provider_name=name,
                validate_keys_func=validate_keys_func,
            )

            self._providers[name] = provider
            return provider

    def get(self, name: str) -> Optional[Any]:
        """Get a provider instance by name."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not found in registry")
        return self._providers[name]()

    def get_loader(self, name: str) -> LazyLoader:
        """Get the loader itself (not the instance)."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not found in registry")
        return self._providers[name]

    def is_available(self, name: str) -> bool:
        """Check if a provider is available."""
        if name not in self._providers:
            return False
        return self._providers[name].is_available()

    def list_providers(self) -> Dict[str, bool]:
        """List all providers and their availability."""
        return {name: loader.is_available() for name, loader in self._providers.items()}

    def force_initialize_all(self) -> Dict[str, bool]:
        """Force initialize all providers and return success status."""
        results = {}
        for name, loader in self._providers.items():
            try:
                loader.force_initialize()
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to initialize provider '{name}': {e}")
                results[name] = False
        return results


# Global registry instance
providers = ProviderRegistry()


# Decorator for easy provider registration
def lazy_provider(
    name: str,
    required_keys: Optional[Set[str]] = None,
    strategy: MissingKeyStrategy = MissingKeyStrategy.WARN,
    warning_message: Optional[str] = None,
    validate_keys_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
):
    """
    Decorator to register a function as a lazy provider.

    Example:
        @lazy_provider("gemini", required_keys={"GOOGLE_API_KEY"})
        def create_gemini_client():
            return GeminiClient(api_key=settings.GOOGLE_API_KEY)
    """

    def decorator(func: Callable[[], T]) -> LazyLoader[T]:
        return providers.register(
            name=name,
            loader_func=func,
            required_keys=required_keys,
            strategy=strategy,
            warning_message=warning_message,
            validate_keys_func=validate_keys_func,
        )

    return decorator
