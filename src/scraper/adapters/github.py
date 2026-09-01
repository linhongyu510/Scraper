"""GitHub REST API adapter for public repository data."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any, cast

from pydantic import HttpUrl, JsonValue

from scraper.exceptions import ConfigurationError, ParseError, RemoteResponseError
from scraper.http import HttpClient
from scraper.models import CollectionResult, Record

API_ROOT = "https://api.github.com"
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
RESOURCES = {"repository", "issues", "releases"}


class GitHubAdapter:
    """Collect repositories, issues, or releases through GitHub's public API."""

    source = "github"

    def __init__(self, http: HttpClient, token: str | None = None) -> None:
        self.http = http
        self.token = token if token is not None else os.getenv("GITHUB_TOKEN")

    def collect(self, *, repo: str, resource: str = "repository") -> CollectionResult:
        """Collect the requested public repository resource."""
        if not REPO_PATTERN.fullmatch(repo):
            raise ConfigurationError("GitHub repo must use the owner/name format")
        if resource not in RESOURCES:
            raise ConfigurationError(
                "GitHub resource must be one of: repository, issues, releases"
            )

        suffix = "" if resource == "repository" else f"/{resource}"
        payload = self.http.get_json(
            f"{API_ROOT}/repos/{repo}{suffix}",
            params=None if resource == "repository" else {"per_page": 100},
            headers=self._headers(),
        )
        if isinstance(payload, dict) and isinstance(payload.get("message"), str):
            raise RemoteResponseError(f"GitHub API error: {payload['message']}")

        if resource == "repository":
            return CollectionResult(records=[self._repository(self._mapping(payload))])

        if not isinstance(payload, list):
            raise ParseError(f"GitHub {resource} response must be a JSON array")
        items = cast(list[object], payload)
        if resource == "issues":
            records = [
                self._issue(self._mapping(item))
                for item in items
                if "pull_request" not in self._mapping(item)
            ]
        else:
            records = [self._release(self._mapping(item)) for item in items]
        return CollectionResult(records=records)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "portfolio-scraper",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _repository(self, item: dict[str, Any]) -> Record:
        owner = self._mapping(item.get("owner"))
        return Record(
            source=self.source,
            id=str(item.get("id", item.get("full_name", ""))),
            title=self._string(item.get("full_name")),
            url=HttpUrl(self._required_url(item)),
            content=self._string(item.get("description")),
            author=self._string(owner.get("login")),
            published_at=self._datetime(item.get("created_at")),
            metadata={
                "kind": "repository",
                "stars": self._integer(item.get("stargazers_count")),
                "forks": self._integer(item.get("forks_count")),
                "language": self._string(item.get("language")),
            },
        )

    def _issue(self, item: dict[str, Any]) -> Record:
        user = self._mapping(item.get("user"))
        labels_value = item.get("labels", [])
        labels = (
            [
                self._string(self._mapping(label).get("name"))
                for label in cast(list[object], labels_value)
            ]
            if isinstance(labels_value, list)
            else []
        )
        return Record(
            source=self.source,
            id=str(item.get("id", item.get("number", ""))),
            title=self._string(item.get("title")),
            url=HttpUrl(self._required_url(item)),
            content=self._string(item.get("body")),
            author=self._string(user.get("login")),
            published_at=self._datetime(item.get("created_at")),
            metadata={
                "kind": "issue",
                "number": self._integer(item.get("number")),
                "state": self._string(item.get("state")),
                "labels": cast(JsonValue, labels),
            },
        )

    def _release(self, item: dict[str, Any]) -> Record:
        author = self._mapping(item.get("author"))
        return Record(
            source=self.source,
            id=str(item.get("id", item.get("tag_name", ""))),
            title=self._string(item.get("name")) or self._string(item.get("tag_name")),
            url=HttpUrl(self._required_url(item)),
            content=self._string(item.get("body")),
            author=self._string(author.get("login")),
            published_at=self._datetime(item.get("published_at")),
            metadata={
                "kind": "release",
                "tag": self._string(item.get("tag_name")),
                "draft": bool(item.get("draft")),
                "prerelease": bool(item.get("prerelease")),
            },
        )

    @staticmethod
    def _mapping(value: object) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ParseError("GitHub API item must be a JSON object")
        return cast(dict[str, Any], value)

    @staticmethod
    def _required_url(item: dict[str, Any]) -> str:
        value = item.get("html_url")
        if not isinstance(value, str) or not value:
            raise ParseError("GitHub API item is missing html_url")
        return value

    @staticmethod
    def _string(value: object) -> str:
        return value if isinstance(value, str) else ""

    @staticmethod
    def _integer(value: object) -> int:
        return value if isinstance(value, int) else 0

    @staticmethod
    def _datetime(value: object) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
