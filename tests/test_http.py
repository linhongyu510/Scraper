import httpx
import pytest

from scraper.exceptions import AuthenticationError, RateLimitError, RemoteResponseError
from scraper.http import HttpClient, redact_headers


def test_client_retries_503_then_returns_json(httpx_mock) -> None:
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(json={"ok": True})

    client = HttpClient(max_retries=1, backoff_factor=0)

    assert client.get_json("https://example.com") == {"ok": True}


def test_client_retries_network_error(httpx_mock) -> None:
    httpx_mock.add_exception(httpx.ConnectError("offline"))
    httpx_mock.add_response(text="ready")

    client = HttpClient(max_retries=1, backoff_factor=0)

    assert client.get_text("https://example.com") == "ready"


def test_redact_headers_hides_credentials() -> None:
    redacted = redact_headers(
        {"Authorization": "Bearer secret", "cookie": "sid=secret", "Accept": "text/plain"}
    )

    assert redacted == {"Authorization": "***", "cookie": "***", "Accept": "text/plain"}


@pytest.mark.parametrize(
    ("status_code", "exception"),
    [(401, AuthenticationError), (403, AuthenticationError), (429, RateLimitError)],
)
def test_client_maps_status_codes(httpx_mock, status_code, exception) -> None:
    httpx_mock.add_response(status_code=status_code)

    with pytest.raises(exception):
        HttpClient(max_retries=0).get_text("https://example.com")


def test_client_rejects_oversized_response(httpx_mock) -> None:
    httpx_mock.add_response(content=b"too large")

    with pytest.raises(RemoteResponseError, match="maximum size"):
        HttpClient(max_response_bytes=3).get_text("https://example.com")
