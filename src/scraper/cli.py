"""Command-line interface."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, cast

import typer

from scraper.adapters.bilibili import BilibiliAdapter
from scraper.adapters.github import GitHubAdapter
from scraper.adapters.rss import RssAdapter
from scraper.adapters.web import WebAdapter
from scraper.analysis.frequency import RecordField, record_frequency
from scraper.analysis.loader import load_records
from scraper.analysis.wordcloud import generate_wordcloud
from scraper.exceptions import ConfigurationError, ScraperError
from scraper.exporters.csv import export_csv
from scraper.exporters.jsonl import export_jsonl
from scraper.http import HttpClient
from scraper.models import CollectionResult

app = typer.Typer(help="Collect and analyze public web data.")
collect_app = typer.Typer(help="Collect records from a source.")
analyze_app = typer.Typer(help="Analyze local records.")
app.add_typer(collect_app, name="collect")
app.add_typer(analyze_app, name="analyze")


def _http_client(timeout: float, retries: int, request_delay: float) -> HttpClient:
    return HttpClient(
        connect_timeout=min(5.0, timeout),
        read_timeout=timeout,
        max_retries=retries,
        request_delay=request_delay,
    )


def _export(result: CollectionResult, output: Path | None) -> None:
    if output is None:
        return
    suffix = output.suffix.lower()
    if suffix == ".jsonl":
        export_jsonl(result.records, output)
    elif suffix == ".csv":
        export_csv(result.records, output)
    else:
        raise ConfigurationError("Output must use .jsonl or .csv")


def _execute_collection(
    operation: Callable[[HttpClient], CollectionResult],
    *,
    output: Path | None,
    timeout: float,
    retries: int,
    request_delay: float,
    fail_fast: bool,
    debug: bool,
) -> None:
    try:
        with _http_client(timeout, retries, request_delay) as http:
            result = operation(http)
        _export(result, output)
        record_word = "record" if len(result.records) == 1 else "records"
        failed_word = "item" if len(result.errors) == 1 else "items"
        typer.echo(
            f"{len(result.records)} {record_word} collected; "
            f"{len(result.errors)} {failed_word} failed"
        )
        for error in result.errors:
            typer.echo(f"warning: {error}", err=True)
        if result.errors:
            raise typer.Exit(code=1 if fail_fast else 2)
    except typer.Exit:
        raise
    except ScraperError as exc:
        if debug:
            raise
        typer.echo(f"error: {exc}")
        raise typer.Exit(code=1) from exc


def _read_stopwords(path: Path | None) -> set[str]:
    if path is None:
        return set()
    try:
        return {
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
    except OSError as exc:
        raise ConfigurationError(f"Unable to read stopwords file {path}: {exc}") from exc


@collect_app.command("bilibili")
def collect_bilibili(
    bvid: Annotated[str, typer.Option(help="Public Bilibili BV identifier.")],
    output: Annotated[Path | None, typer.Option("-o", "--output")] = None,
    timeout: Annotated[float, typer.Option(min=0.1)] = 20.0,
    retries: Annotated[int, typer.Option(min=0, max=10)] = 2,
    request_delay: Annotated[float, typer.Option(min=0.0)] = 0.0,
    fail_fast: Annotated[bool, typer.Option()] = False,
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """Collect public video metadata and XML danmaku."""
    _execute_collection(
        lambda http: BilibiliAdapter(http).collect(bvid=bvid),
        output=output,
        timeout=timeout,
        retries=retries,
        request_delay=request_delay,
        fail_fast=fail_fast,
        debug=debug,
    )


@collect_app.command("github")
def collect_github(
    repo: Annotated[str, typer.Option(help="Repository in owner/name form.")],
    resource: Annotated[str, typer.Option(help="repository, issues, or releases.")] = "repository",
    output: Annotated[Path | None, typer.Option("-o", "--output")] = None,
    timeout: Annotated[float, typer.Option(min=0.1)] = 20.0,
    retries: Annotated[int, typer.Option(min=0, max=10)] = 2,
    request_delay: Annotated[float, typer.Option(min=0.0)] = 0.0,
    fail_fast: Annotated[bool, typer.Option()] = False,
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """Collect a GitHub repository, its issues, or its releases."""
    _execute_collection(
        lambda http: GitHubAdapter(http).collect(repo=repo, resource=resource),
        output=output,
        timeout=timeout,
        retries=retries,
        request_delay=request_delay,
        fail_fast=fail_fast,
        debug=debug,
    )


@collect_app.command("rss")
def collect_rss(
    url: Annotated[str, typer.Option(help="Public RSS or Atom feed URL.")],
    output: Annotated[Path | None, typer.Option("-o", "--output")] = None,
    timeout: Annotated[float, typer.Option(min=0.1)] = 20.0,
    retries: Annotated[int, typer.Option(min=0, max=10)] = 2,
    request_delay: Annotated[float, typer.Option(min=0.0)] = 0.0,
    fail_fast: Annotated[bool, typer.Option()] = False,
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """Collect entries from an RSS or Atom feed."""
    _execute_collection(
        lambda http: RssAdapter(http).collect(url=url),
        output=output,
        timeout=timeout,
        retries=retries,
        request_delay=request_delay,
        fail_fast=fail_fast,
        debug=debug,
    )


@collect_app.command("web")
def collect_web(
    url: Annotated[str, typer.Option(help="Public static page URL.")],
    item: Annotated[str, typer.Option(help="CSS selector for repeated items.")],
    title: Annotated[str, typer.Option(help="Title selector within each item.")],
    content: Annotated[str, typer.Option(help="Content selector within each item.")],
    link: Annotated[str, typer.Option(help="Link selector within each item.")],
    output: Annotated[Path | None, typer.Option("-o", "--output")] = None,
    timeout: Annotated[float, typer.Option(min=0.1)] = 20.0,
    retries: Annotated[int, typer.Option(min=0, max=10)] = 2,
    request_delay: Annotated[float, typer.Option(min=0.0)] = 0.0,
    fail_fast: Annotated[bool, typer.Option()] = False,
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """Collect repeated elements from a static HTML page."""
    _execute_collection(
        lambda http: WebAdapter(http).collect(
            url=url,
            item=item,
            title=title,
            content=content,
            link=link,
        ),
        output=output,
        timeout=timeout,
        retries=retries,
        request_delay=request_delay,
        fail_fast=fail_fast,
        debug=debug,
    )


def _field(value: str) -> RecordField:
    if value not in {"title", "content", "author"}:
        raise ConfigurationError("Field must be title, content, or author")
    return cast(RecordField, value)


@analyze_app.command("frequency")
def analyze_frequency(
    input_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    field: Annotated[str, typer.Option()] = "content",
    stopwords: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    min_length: Annotated[int, typer.Option(min=1)] = 1,
    top: Annotated[int, typer.Option(min=1)] = 50,
    output_format: Annotated[str, typer.Option("--format")] = "table",
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """Print word frequencies from local JSONL, CSV, or text."""
    try:
        rows = record_frequency(
            load_records(input_path),
            field=_field(field),
            stopwords=_read_stopwords(stopwords),
            min_length=min_length,
            top=top,
        )
        if output_format == "json":
            typer.echo(json.dumps(dict(rows), ensure_ascii=False))
        elif output_format == "table":
            for word, count in rows:
                typer.echo(f"{word}\t{count}")
        else:
            raise ConfigurationError("Format must be table or json")
    except ScraperError as exc:
        if debug:
            raise
        typer.echo(f"error: {exc}")
        raise typer.Exit(code=1) from exc


@analyze_app.command("wordcloud")
def analyze_wordcloud(
    input_path: Annotated[
        Path,
        typer.Argument(exists=True, dir_okay=False, readable=True),
    ],
    output: Annotated[Path, typer.Option("-o", "--output")] = Path("wordcloud.png"),
    field: Annotated[str, typer.Option()] = "content",
    stopwords: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    min_length: Annotated[int, typer.Option(min=1)] = 1,
    top: Annotated[int, typer.Option(min=1)] = 200,
    font_path: Annotated[Path | None, typer.Option()] = None,
    debug: Annotated[bool, typer.Option()] = False,
) -> None:
    """Generate a PNG word cloud from local records."""
    try:
        rows = record_frequency(
            load_records(input_path),
            field=_field(field),
            stopwords=_read_stopwords(stopwords),
            min_length=min_length,
            top=top,
        )
        generate_wordcloud(rows, output, font_path=font_path)
        typer.echo(f"Word cloud written to {output}")
    except ScraperError as exc:
        if debug:
            raise
        typer.echo(f"error: {exc}")
        raise typer.Exit(code=1) from exc
