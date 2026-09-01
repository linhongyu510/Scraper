"""Domain exceptions surfaced by the CLI."""


class ScraperError(Exception):
    """Base class for expected scraper failures."""


class ConfigurationError(ScraperError):
    """Raised when user-provided configuration is invalid."""


class AuthenticationError(ScraperError):
    """Raised when a remote service rejects credentials."""


class RateLimitError(ScraperError):
    """Raised when a remote service rate-limits a request."""


class RemoteResponseError(ScraperError):
    """Raised for unsuccessful or oversized remote responses."""


class ParseError(ScraperError):
    """Raised when remote or local content cannot be parsed."""


class ExportError(ScraperError):
    """Raised when records cannot be exported."""
