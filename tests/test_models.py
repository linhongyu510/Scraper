import pytest
from pydantic import ValidationError

from scraper.models import Record


def test_record_rejects_missing_source() -> None:
    with pytest.raises(ValidationError):
        Record(source="", id="1", url="https://example.com", content="hello")


def test_record_accepts_json_metadata() -> None:
    record = Record(
        source="rss",
        id="1",
        title="Post",
        url="https://example.com/1",
        content="hello",
        metadata={"tags": ["python"]},
    )

    assert record.metadata["tags"] == ["python"]
