import json
from pathlib import Path

import pytest

from scraper.adapters.github import GitHubAdapter
from scraper.exceptions import ConfigurationError, RemoteResponseError

FIXTURES = Path(__file__).parents[1] / "fixtures"


class FakeHttp:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.headers: dict[str, str] = {}

    def get_json(self, _url: str, **kwargs: object) -> object:
        self.headers = kwargs.get("headers", {})  # type: ignore[assignment]
        return self.payload


def load(name: str) -> object:
    return json.loads((FIXTURES / name).read_text())


def test_github_issues_become_records_and_pull_requests_are_filtered() -> None:
    result = GitHubAdapter(FakeHttp(load("github_issues.json")), token=None).collect(
        repo="owner/repo", resource="issues"
    )

    assert len(result.records) == 1
    assert result.records[0].metadata["kind"] == "issue"
    assert result.records[0].metadata["labels"] == ["bug"]


def test_github_repository_becomes_record() -> None:
    result = GitHubAdapter(FakeHttp(load("github_repository.json"))).collect(
        repo="owner/repo", resource="repository"
    )

    assert result.records[0].metadata["stars"] == 42


def test_github_release_becomes_record() -> None:
    result = GitHubAdapter(FakeHttp(load("github_releases.json"))).collect(
        repo="owner/repo", resource="releases"
    )

    assert result.records[0].id == "301"
    assert result.records[0].metadata["kind"] == "release"


def test_github_token_is_sent_as_bearer_header() -> None:
    http = FakeHttp(load("github_repository.json"))

    GitHubAdapter(http, token="test-token").collect(repo="owner/repo", resource="repository")

    assert http.headers["Authorization"] == "Bearer test-token"


def test_github_rejects_invalid_resource() -> None:
    with pytest.raises(ConfigurationError, match="resource"):
        GitHubAdapter(FakeHttp([])).collect(repo="owner/repo", resource="pulls")


def test_github_api_message_is_mapped() -> None:
    with pytest.raises(RemoteResponseError, match="Bad credentials"):
        GitHubAdapter(FakeHttp({"message": "Bad credentials"})).collect(
            repo="owner/repo", resource="issues"
        )
