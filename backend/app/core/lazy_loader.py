from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Generic, List, Optional, Set, TypeVar

from app.config.loggers import app_logger as logger
from app.utils.exceptions import ConfigurationError

T = TypeVar("T")


class MissingKeyStrategy(Enum):
    """Strategy for handling missing keys"""

    ERROR = "error"  # Raise exception on get() call
    WARN = "warn"  # Log warning on registration and return None on get()
    WARN_ONCE = "warn_once"  # Log warning once on registration and return None on get()
    SILENT = "silent"  # Return None silently on get()


class LazyLoader(Generic[T]):
    """
    Lazy loader that defers provider initialization until first get() access.

    Features:
    - Thread-safe singleton pattern per loader
    - Configurable error handling for missing values
    - Validation caching to avoid repeated checks
    - Flexible warning system at registration time
    - Type safety with generics
    - Support for global context providers (like Cloudinary)
    """

    def __init__(
        self,
        loader_func: Callable[[], T],
        required_keys: Optional[List[Any]] = None,
        strategy: MissingKeyStrategy = MissingKeyStrategy.ERROR,
        warning_message: Optional[str] = None,
        provider_name: Optional[str] = None,
        validate_values_func: Optional[Callable[[List[Any]], bool]] = None,
        is_global_context: bool = False,
        auto_initialize: bool = False,
    ):
        """
        Initialize lazy loader.

        Args:
            loader_func: Function that creates the provider instance or configures global context
            required_keys: List of direct values that are required (can be None individually)
            strategy: How to handle missing values
            warning_message: Custom warning message
            provider_name: Name for logging/error messages
            validate_values_func: Custom validation function for the values
            is_global_context: If True, provider configures global context instead of returning instance
            auto_initialize: If True, automatically initialize at registration time when values are available
        """
        self.loader_func = loader_func
        self.required_keys = required_keys or []
        self.strategy = strategy
        self.warning_message = warning_message
        self.provider_name = provider_name or loader_func.__name__
        self.validate_values_func = validate_values_func
        self.is_global_context = is_global_context
        self.auto_initialize = auto_initialize

        self._instance: Optional[T] = None
        self._is_configured = False  # For global context providers
        self._lock = Lock()
        self._warned_indices: Set[int] = (
            set()
        )  # Track warned value indices for WARN_ONCE

        # Check availability at registration time and log warnings
        self._check_availability_and_warn()

        # Auto-initialize if enabled and values are available
        if self.auto_initialize and self.is_available():
            try:
                self._initialize()
                logger.info(
                    f"Auto-initialized provider '{self.provider_name}' at registration time"
                )
            except Exception as e:
                if self.strategy == MissingKeyStrategy.ERROR:
                    raise
                else:
                    logger.warning(
                        f"Auto-initialization failed for '{self.provider_name}': {e}"
                    )

    def _check_availability_and_warn(self):
        """Check availability at registration time and log warnings if needed."""
        missing_indices = self._check_required_keys()

        if not missing_indices:
            # All values available
            if self.validate_values_func and not self.validate_values_func(
                self.required_keys
            ):
                # Custom validation failed
                message = f"Value validation failed for provider '{self.provider_name}'"
                if self.strategy in [
                    MissingKeyStrategy.WARN,
                    MissingKeyStrategy.WARN_ONCE,
                ]:
                    self._log_warning(message)
            else:
                if not self.auto_initialize:
                    logger.info(
                        f"Provider '{self.provider_name}' is ready for lazy initialization"
                    )
            return

        # Missing values found - handle according to strategy
        if self.strategy == MissingKeyStrategy.SILENT:
            # Don't log anything
            return

        indices_str = ", ".join(f"index {i}" for i in missing_indices)
        missing_values = [self.required_keys[i] for i in missing_indices]

        message = (
            self.warning_message
            or f"Provider '{self.provider_name}' missing required values at {indices_str}: {missing_values}"
        )

        if self.strategy in [MissingKeyStrategy.WARN, MissingKeyStrategy.WARN_ONCE]:
            self._log_warning(f"Registration warning: {message}")
            if self.strategy == MissingKeyStrategy.WARN_ONCE:
                self._warned_indices.update(missing_indices)
        elif not self.auto_initialize:
            # Only log info about readiness if not auto-initializing
            # (auto-initialize will log its own success/failure message)
            logger.info(
                f"Provider '{self.provider_name}' registered but will initialize on first access"
            )

    def get(self) -> Optional[T]:
        """Get the provider instance, initializing lazily on first call."""
        # Quick check without lock for already initialized instances
        if self.is_global_context and self._is_configured:
            return True  # type: ignore
        elif not self.is_global_context and self._instance is not None:
            return self._instance

        with self._lock:
            # Double-check locking pattern
            if self.is_global_context and self._is_configured:
                return True  # type: ignore
            elif not self.is_global_context and self._instance is not None:
                return self._instance

            return self._initialize()

    def _initialize(self) -> Optional[T]:
        """Initialize the provider instance or configure global context."""
        # Check if required values are valid
        missing_indices = self._check_required_keys()
        if missing_indices:
            return self._handle_missing_values_on_get(missing_indices)

        # Validate values if custom validator provided
        if self.validate_values_func:
            if not self.validate_values_func(self.required_keys):
                return self._handle_validation_failure_on_get()

        try:
            if self.is_global_context:
                # For global context providers, call the function for side effects
                self.loader_func()
                self._is_configured = True
                logger.info(
                    f"Successfully configured global provider: {self.provider_name}"
                )
                return True  # type: ignore
            else:
                # For instance-based providers, store and return the instance
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
                return None

    def _check_required_keys(self) -> Set[int]:
        """Check which required values are missing/invalid."""
        missing_indices = set()
        for i, value in enumerate(self.required_keys):
            if self._is_value_missing(value):
                missing_indices.add(i)
        return missing_indices

    def _is_value_missing(self, value: Any) -> bool:
        """Check if a value is considered missing/invalid."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        return False

    def _handle_missing_values_on_get(self, missing_indices: Set[int]) -> Optional[T]:
        """Handle missing values when get() is called."""
        if self.strategy == MissingKeyStrategy.ERROR:
            indices_str = ", ".join(f"index {i}" for i in missing_indices)
            missing_values = [self.required_keys[i] for i in missing_indices]
            raise ConfigurationError(
                f"Cannot initialize provider '{self.provider_name}' - missing values at {indices_str}: {missing_values}"
            )

        # For non-error strategies, just return None (warning already logged at registration)
        return None

    def _handle_validation_failure_on_get(self) -> Optional[T]:
        """Handle custom validation failure when get() is called."""
        if self.strategy == MissingKeyStrategy.ERROR:
            raise ConfigurationError(
                f"Cannot initialize provider '{self.provider_name}' - value validation failed"
            )

        # For non-error strategies, just return None (warning already logged at registration)
        return None

    def _log_warning(self, message: str):
        """Log warning message."""
        logger.warning(f"[LazyLoader] {message}")

    def is_available(self) -> bool:
        """Check if the provider is available without initializing it."""
        missing_indices = self._check_required_keys()
        if missing_indices:
            return False

        # If custom validator exists, check it too
        if self.validate_values_func:
            return self.validate_values_func(self.required_keys)

        return True

    def is_initialized(self) -> bool:
        """Check if the provider is already initialized."""
        if self.is_global_context:
            return self._is_configured
        else:
            return self._instance is not None

    def reset(self):
        """Reset the loader (useful for testing)."""
        with self._lock:
            self._instance = None
            self._is_configured = False


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
        required_keys: Optional[List[Any]] = None,
        strategy: MissingKeyStrategy = MissingKeyStrategy.WARN,
        warning_message: Optional[str] = None,
        validate_values_func: Optional[Callable[[List[Any]], bool]] = None,
        is_global_context: bool = False,
        auto_initialize: bool = False,
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
                validate_values_func=validate_values_func,
                is_global_context=is_global_context,
                auto_initialize=auto_initialize,
            )

            self._providers[name] = provider
            return provider

    def get(self, name: str) -> Optional[Any]:
        """Get a provider instance by name - this triggers lazy initialization."""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not found in registry")
        return self._providers[name].get()

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

    def is_initialized(self, name: str) -> bool:
        """Check if a provider is already initialized."""
        if name not in self._providers:
            return False
        return self._providers[name].is_initialized()

    def list_providers(self) -> Dict[str, Dict[str, bool]]:
        """List all providers with their status."""
        return {
            name: {
                "available": loader.is_available(),
                "initialized": loader.is_initialized(),
                "is_global_context": loader.is_global_context,
            }
            for name, loader in self._providers.items()
        }


# Global registry instance
providers = ProviderRegistry()


# Decorator for easy provider registration
def lazy_provider(
    name: str,
    required_keys: Optional[List[Any]] = None,
    strategy: MissingKeyStrategy = MissingKeyStrategy.WARN,
    warning_message: Optional[str] = None,
    validate_values_func: Optional[Callable[[List[Any]], bool]] = None,
    is_global_context: bool = False,
    auto_initialize: bool = False,
):
    """
    Decorator to register a function as a lazy provider.

    Returns a callable that, when called, registers the provider.
    This allows you to control when registration happens (e.g., in FastAPI lifespan).

    Examples:
        # Instance-based provider (returns an object)
        @lazy_provider("gemini", required_keys=[settings.GOOGLE_API_KEY])
        def create_gemini_client():
            return GeminiClient(api_key=settings.GOOGLE_API_KEY)

        # Global context provider (configures global state) with auto-initialization
        @lazy_provider(
            "cloudinary",
            required_keys=[settings.CLOUDINARY_CLOUD_NAME, settings.CLOUDINARY_API_KEY],
            is_global_context=True,
            auto_initialize=True
        )
        def configure_cloudinary():
            import cloudinary
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )

        # In FastAPI lifespan:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Register providers when you want them
            create_gemini_client()  # This registers the provider
            configure_cloudinary()  # This registers and potentially auto-initializes
            yield
    """

    def decorator(func: Callable[[], T]) -> Callable[[], LazyLoader[T]]:
        def register_provider() -> LazyLoader[T]:
            return providers.register(
                name=name,
                loader_func=func,
                required_keys=required_keys,
                strategy=strategy,
                warning_message=warning_message,
                validate_values_func=validate_values_func,
                is_global_context=is_global_context,
                auto_initialize=auto_initialize,
            )

        return register_provider

    return decorator
