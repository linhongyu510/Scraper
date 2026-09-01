from pathlib import Path

from pydantic import HttpUrl
from typer.testing import CliRunner

from scraper.cli import app
from scraper.models import CollectionResult, Record


runner = CliRunner()


def test_cli_help_lists_command_groups() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "collect" in result.stdout
    assert "analyze" in result.stdout


class FakeRssAdapter:
    def __init__(self, _http: object) -> None:
        pass

    def collect(self, **_kwargs: object) -> CollectionResult:
        return CollectionResult(
            records=[
                Record(
                    source="rss",
                    id="1",
                    url=HttpUrl("https://example.com/1"),
                    content="fixture",
                )
            ]
        )


class PartiallyFailingAdapter:
    def __init__(self, _http: object, token: str | None = None) -> None:
        pass

    def collect(self, **_kwargs: object) -> CollectionResult:
        return CollectionResult(
            records=[
                Record(
                    source="github",
                    id="1",
                    url=HttpUrl("https://github.com/o/r/issues/1"),
                )
            ],
            errors=["issue 2 failed"],
        )


def test_collect_rss_writes_jsonl(monkeypatch, tmp_path) -> None:
    output = tmp_path / "feed.jsonl"
    monkeypatch.setattr("scraper.cli.RssAdapter", FakeRssAdapter)

    result = runner.invoke(
        app,
        ["collect", "rss", "--url", "https://example.com/feed", "-o", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()


def test_partial_failure_returns_exit_code_two(monkeypatch) -> None:
    monkeypatch.setattr("scraper.cli.GitHubAdapter", PartiallyFailingAdapter)

    result = runner.invoke(
        app,
        ["collect", "github", "--repo", "o/r", "--resource", "issues"],
    )

    assert result.exit_code == 2
    assert "1 record collected; 1 item failed" in result.stdout


def test_analysis_frequency_reads_local_records(tmp_path) -> None:
    source = tmp_path / "input.txt"
    source.write_text("海洋 海洋 地球\n", encoding="utf-8")

    result = runner.invoke(app, ["analyze", "frequency", str(source), "--top", "1"])

    assert result.exit_code == 0
    assert "海洋\t2" in result.stdout


def test_collect_rejects_unknown_output_extension(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("scraper.cli.RssAdapter", FakeRssAdapter)
    output = Path(tmp_path) / "feed.xml"

    result = runner.invoke(
        app,
        ["collect", "rss", "--url", "https://example.com/feed", "-o", str(output)],
    )

    assert result.exit_code == 1
    assert "Output must use .jsonl or .csv" in result.stdout
