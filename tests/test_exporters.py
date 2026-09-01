import csv
import json

import pytest
from pydantic import HttpUrl

from scraper.analysis.loader import load_records
from scraper.exceptions import ExportError, ParseError
from scraper.exporters.csv import export_csv
from scraper.exporters.jsonl import export_jsonl
from scraper.models import Record


@pytest.fixture
def records() -> list[Record]:
    return [
        Record(
            source="rss",
            id="post-1",
            title="中文标题",
            url=HttpUrl("https://example.com/1"),
            content="hello",
            metadata={"tags": ["python", "采集"]},
        )
    ]


def test_jsonl_round_trip_preserves_metadata(tmp_path, records) -> None:
    output = tmp_path / "records.jsonl"

    export_jsonl(records, output)

    assert load_records(output) == records


def test_csv_round_trip_preserves_metadata(tmp_path, records) -> None:
    output = tmp_path / "records.csv"

    export_csv(records, output)

    assert load_records(output) == records
    with output.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["metadata"])["tags"] == ["python", "采集"]


def test_text_loader_creates_local_records(tmp_path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("first\n\n第二行\n", encoding="utf-8")

    records = load_records(source)

    assert [record.content for record in records] == ["first", "第二行"]


def test_loader_reports_invalid_jsonl_line(tmp_path) -> None:
    source = tmp_path / "broken.jsonl"
    source.write_text("{}\nnot-json\n", encoding="utf-8")

    with pytest.raises(ParseError, match=r"broken\.jsonl:1"):
        load_records(source)


def test_exporter_wraps_filesystem_errors(tmp_path, records) -> None:
    with pytest.raises(ExportError):
        export_jsonl(records, tmp_path)
