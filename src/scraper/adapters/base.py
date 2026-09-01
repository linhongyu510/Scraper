"""Adapter contract."""

from typing import Protocol

from scraper.models import CollectionResult


class SourceAdapter(Protocol):
    """Contract implemented by every public-data source."""

    source: str

    def collect(self, **kwargs: object) -> CollectionResult:
        """Collect normalized records from the source."""
        ...
