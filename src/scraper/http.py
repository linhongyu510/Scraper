"""Reliable synchronous HTTP access with bounded retries."""

from __future__ import annotations

import time
from collections.abc import Mapping
from email.utils import parsedate_to_datetime
from typing import cast

import httpx

from scraper.exceptions import (
    AuthenticationError,
    ParseError,
    RateLimitError,
    RemoteResponseError,
)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
SENSITIVE_HEADERS = {"authorization", "cookie", "proxy-authorization", "x-api-key"}
QueryValue = str | int | float | bool | None


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Return headers safe for diagnostic output."""
    return {
        name: "***" if name.lower() in SENSITIVE_HEADERS else value
        for name, value in headers.items()
    }


class HttpClient:
    """Small httpx wrapper with predictable failure semantics."""

    def __init__(
        self,
        *,
        connect_timeout: float = 5.0,
        read_timeout: float = 20.0,
        max_response_bytes: int = 10 * 1024 * 1024,
        max_retries: int = 2,
        backoff_factor: float = 0.5,
        request_delay: float = 0.0,
        client: httpx.Client | None = None,
    ) -> None:
        if max_retries < 0 or max_response_bytes < 1 or request_delay < 0:
            raise ValueError("retry count, response size, and request delay must be non-negative")
        timeout = httpx.Timeout(
            connect=connect_timeout,
            read=read_timeout,
            write=read_timeout,
            pool=connect_timeout,
        )
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=True)
        self._owns_client = client is None
        self.max_response_bytes = max_response_bytes
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.request_delay = request_delay
        self._last_request_at: float | None = None

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying client when this instance created it."""
        if self._owns_client:
            self._client.close()

    def get_text(
        self,
        url: str,
        *,
        params: Mapping[str, QueryValue] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> str:
        """GET a bounded response and decode it as text."""
        return self._request(url, params=params, headers=headers).text

    def get_json(
        self,
        url: str,
        *,
        params: Mapping[str, QueryValue] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> object:
        """GET a bounded response and decode its JSON value."""
        response = self._request(url, params=params, headers=headers)
        try:
            return cast(object, response.json())
        except ValueError as exc:
            raise ParseError(f"Invalid JSON returned by {url}") from exc

    def _request(
        self,
        url: str,
        *,
        params: Mapping[str, QueryValue] | None,
        headers: Mapping[str, str] | None,
    ) -> httpx.Response:
        for attempt in range(self.max_retries + 1):
            self._respect_request_delay()
            try:
                response = self._client.get(url, params=params, headers=headers)
            except httpx.RequestError as exc:
                if attempt == self.max_retries:
                    raise RemoteResponseError(f"Request failed for {url}: {exc}") from exc
                self._sleep_before_retry(attempt, None)
                continue

            if response.status_code in RETRYABLE_STATUS_CODES and attempt < self.max_retries:
                self._sleep_before_retry(attempt, response.headers.get("Retry-After"))
                continue

            self._raise_for_status(response)
            if len(response.content) > self.max_response_bytes:
                raise RemoteResponseError(
                    f"Response from {url} exceeds maximum size of {self.max_response_bytes} bytes"
                )
            return response

        raise AssertionError("retry loop exited unexpectedly")

    def _respect_request_delay(self) -> None:
        now = time.monotonic()
        if self._last_request_at is not None:
            time.sleep(max(0.0, self.request_delay - (now - self._last_request_at)))
        self._last_request_at = time.monotonic()

    def _sleep_before_retry(self, attempt: int, retry_after: str | None) -> None:
        delay = self._parse_retry_after(retry_after)
        time.sleep(delay if delay is not None else self.backoff_factor * (2**attempt))

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                return max(0.0, retry_at.timestamp() - time.time())
            except (TypeError, ValueError, OverflowError):
                return None

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        message = f"Remote server returned HTTP {status} for {response.request.url}"
        if status in {401, 403}:
            raise AuthenticationError(message)
        if status == 429:
            raise RateLimitError(message)
        if status >= 400:
            raise RemoteResponseError(message)
