"""RSS and Atom feed adapter."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, cast

import feedparser  # type: ignore[import-untyped]
from pydantic import HttpUrl, JsonValue

from scraper.exceptions import ParseError
from scraper.http import HttpClient
from scraper.models import CollectionResult, Record


class RssAdapter:
    """Parse RSS and Atom feeds into normalized records."""

    source = "rss"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def collect(self, *, url: str) -> CollectionResult:
        """Fetch and parse all entries in a feed."""
        parsed = cast(dict[str, Any], feedparser.parse(self.http.get_text(url)))
        entries_value = parsed.get("entries", [])
        if not isinstance(entries_value, list):
            raise ParseError("Feed entries must be a list")
        entries = cast(list[object], entries_value)
        if parsed.get("bozo") and not entries:
            raise ParseError(f"Unable to parse feed: {parsed.get('bozo_exception', 'invalid XML')}")

        records = [self._record(self._mapping(entry), feed_url=url) for entry in entries]
        return CollectionResult(records=records)

    def _record(self, entry: dict[str, Any], *, feed_url: str) -> Record:
        title = self._string(entry.get("title"))
        content = self._content(entry)
        link = self._string(entry.get("link")) or feed_url
        identifier = self._string(entry.get("id")) or self._stable_id(link, title, content)
        author = self._string(entry.get("author"))
        tags_value = entry.get("tags", [])
        tags = (
            [
                self._string(self._mapping(tag).get("term"))
                for tag in cast(list[object], tags_value)
            ]
            if isinstance(tags_value, list)
            else []
        )
        return Record(
            source=self.source,
            id=identifier,
            title=title,
            url=HttpUrl(link),
            content=content,
            author=author,
            published_at=self._published_at(entry),
            metadata={"kind": "entry", "tags": cast(JsonValue, tags)},
        )

    @staticmethod
    def _content(entry: dict[str, Any]) -> str:
        summary = entry.get("summary")
        if isinstance(summary, str):
            return summary
        values = entry.get("content")
        if isinstance(values, list) and values:
            first = values[0]
            if isinstance(first, dict) and isinstance(first.get("value"), str):
                return cast(str, first["value"])
        return ""

    @staticmethod
    def _published_at(entry: dict[str, Any]) -> datetime | None:
        value = entry.get("published_parsed") or entry.get("updated_parsed")
        if isinstance(value, tuple) and len(value) >= 6:
            try:
                parts = cast(tuple[int, ...], value)
                return datetime(
                    parts[0],
                    parts[1],
                    parts[2],
                    parts[3],
                    parts[4],
                    parts[5],
                    tzinfo=timezone.utc,
                )
            except (TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _stable_id(*parts: str) -> str:
        return hashlib.sha256("\0".join(parts).encode()).hexdigest()[:20]

    @staticmethod
    def _mapping(value: object) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ParseError("Feed entry must be an object")
        return cast(dict[str, Any], value)

    @staticmethod
    def _string(value: object) -> str:
        return value if isinstance(value, str) else ""
