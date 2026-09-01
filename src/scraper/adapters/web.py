"""Static HTML adapter driven by CSS selectors."""

from __future__ import annotations

import hashlib
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl
from soupsieve.util import SelectorSyntaxError

from scraper.exceptions import ConfigurationError, ParseError
from scraper.http import HttpClient
from scraper.models import CollectionResult, Record


class WebAdapter:
    """Extract repeated records from static HTML."""

    source = "web"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def collect(
        self,
        *,
        url: str,
        item: str,
        title: str,
        content: str,
        link: str,
    ) -> CollectionResult:
        """Collect elements matched by the supplied CSS selectors."""
        soup = BeautifulSoup(self.http.get_text(url), "html.parser")
        try:
            items = soup.select(item)
        except SelectorSyntaxError as exc:
            raise ConfigurationError(f"Invalid item CSS selector: {item}") from exc
        if not items:
            raise ParseError(f"CSS selector {item!r} matched no items")

        records: list[Record] = []
        for element in items:
            title_element = self._select_one(element, title)
            content_element = self._select_one(element, content)
            link_element = self._select_one(element, link)
            href = link_element.get("href") if link_element else None
            absolute_url = urljoin(url, href if isinstance(href, str) else "")
            title_text = title_element.get_text(" ", strip=True) if title_element else ""
            content_text = content_element.get_text(" ", strip=True) if content_element else ""
            stable_id = hashlib.sha256(f"{absolute_url}\0{content_text}".encode()).hexdigest()[:20]
            records.append(
                Record(
                    source=self.source,
                    id=stable_id,
                    title=title_text,
                    url=HttpUrl(absolute_url),
                    content=content_text,
                    metadata={"kind": "web-item", "selector": item},
                )
            )
        return CollectionResult(records=records)

    @staticmethod
    def _select_one(element: Tag, selector: str) -> Tag | None:
        try:
            return element.select_one(selector)
        except SelectorSyntaxError as exc:
            raise ConfigurationError(f"Invalid CSS selector: {selector}") from exc
