"""Bilibili public video metadata and danmaku adapter."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, cast

from pydantic import HttpUrl

from scraper.exceptions import ConfigurationError, ParseError, RemoteResponseError
from scraper.http import HttpClient
from scraper.models import CollectionResult, Record

VIEW_API = "https://api.bilibili.com/x/web-interface/view"
DANMAKU_API = "https://comment.bilibili.com/{cid}.xml"
BVID_PATTERN = re.compile(r"^BV[0-9A-Za-z]{10}$")


class BilibiliAdapter:
    """Collect public metadata and XML danmaku without account cookies."""

    source = "bilibili"

    def __init__(self, http: HttpClient) -> None:
        self.http = http

    def collect(self, *, bvid: str) -> CollectionResult:
        """Collect one video record followed by its public danmaku records."""
        if not BVID_PATTERN.fullmatch(bvid):
            raise ConfigurationError("Bilibili video ID must be a valid BV identifier")

        payload = self.http.get_json(VIEW_API, params={"bvid": bvid})
        root = self._mapping(payload, "Bilibili API response")
        code = root.get("code")
        if code != 0:
            message = root.get("message", "unknown API error")
            raise RemoteResponseError(f"Bilibili API error {code}: {message}")

        data = self._mapping(root.get("data"), "Bilibili video data")
        title = self._string(data.get("title"))
        owner = self._mapping(data.get("owner"), "Bilibili video owner")
        pages = data.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ParseError("Bilibili video response does not contain any pages")

        published_at = self._datetime(data.get("pubdate"))
        video_url = f"https://www.bilibili.com/video/{bvid}"
        records = [
            Record(
                source=self.source,
                id=bvid,
                title=title,
                url=HttpUrl(video_url),
                content=self._string(data.get("desc")),
                author=self._string(owner.get("name")),
                published_at=published_at,
                metadata={"kind": "video", "page_count": len(pages)},
            )
        ]

        for page in pages:
            page_data = self._mapping(page, "Bilibili page data")
            cid = page_data.get("cid")
            if not isinstance(cid, int):
                raise ParseError("Bilibili page is missing a numeric cid")
            xml = self.http.get_text(DANMAKU_API.format(cid=cid))
            records.extend(self._parse_danmaku(xml, bvid=bvid, cid=cid, url=video_url))

        return CollectionResult(records=records)

    def _parse_danmaku(self, xml: str, *, bvid: str, cid: int, url: str) -> list[Record]:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            raise ParseError(f"Invalid Bilibili danmaku XML for cid {cid}") from exc

        records: list[Record] = []
        for index, element in enumerate(root.findall(".//d"), start=1):
            attributes = element.get("p", "").split(",")
            content = element.text or ""
            published_at = self._datetime(attributes[4] if len(attributes) > 4 else None)
            offset = self._float(attributes[0] if attributes else None)
            records.append(
                Record(
                    source=self.source,
                    id=f"{bvid}:{cid}:{index}",
                    title="",
                    url=HttpUrl(url),
                    content=content,
                    published_at=published_at,
                    metadata={
                        "kind": "danmaku",
                        "cid": cid,
                        "offset_seconds": offset,
                    },
                )
            )
        return records

    @staticmethod
    def _mapping(value: object, label: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ParseError(f"{label} must be a JSON object")
        return cast(dict[str, Any], value)

    @staticmethod
    def _string(value: object) -> str:
        return value if isinstance(value, str) else ""

    @staticmethod
    def _datetime(value: object) -> datetime | None:
        try:
            return datetime.fromtimestamp(float(cast(Any, value)), tz=timezone.utc)
        except (TypeError, ValueError, OSError, OverflowError):
            return None

    @staticmethod
    def _float(value: object) -> float | None:
        try:
            return float(cast(Any, value))
        except (TypeError, ValueError):
            return None
