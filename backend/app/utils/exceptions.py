class FetchError(Exception):
    """Exception raised for errors during web fetching operations."""

    def __init__(self, message, status_code=None, url=None):
        self.message = message
        self.status_code = status_code
        self.url = url
        super().__init__(self.message)

    def __str__(self):
        """Enhanced string representation with additional context if available."""
        base_message = self.message
        if self.status_code:
            base_message += f" (Status code: {self.status_code})"
        if self.url:
            base_message += f" - URL: {self.url}"
        return base_message


class InfisicalConfigError(Exception):
    """Exception raised for errors related to Infisical configuration."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
