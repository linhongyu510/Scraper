import json
from pathlib import Path

import pytest

from scraper.adapters.bilibili import BilibiliAdapter
from scraper.exceptions import ConfigurationError, ParseError, RemoteResponseError

FIXTURES = Path(__file__).parents[1] / "fixtures"


class FakeHttp:
    def __init__(self, *, view: object | None = None, danmaku: str | None = None) -> None:
        self.view = view or json.loads((FIXTURES / "bilibili_view.json").read_text())
        self.danmaku = (
            danmaku if danmaku is not None else (FIXTURES / "bilibili_danmaku.xml").read_text()
        )

    def get_json(self, url: str, **_kwargs: object) -> object:
        return self.view

    def get_text(self, url: str, **_kwargs: object) -> str:
        return self.danmaku


def test_collects_video_and_danmaku_records() -> None:
    result = BilibiliAdapter(FakeHttp()).collect(bvid="BV1xx411c7mD")

    assert result.errors == []
    assert [record.metadata["kind"] for record in result.records] == [
        "video",
        "danmaku",
        "danmaku",
    ]
    assert all(record.source == "bilibili" for record in result.records)


def test_empty_danmaku_still_returns_video() -> None:
    result = BilibiliAdapter(FakeHttp(danmaku="<i />")).collect(bvid="BV1xx411c7mD")

    assert len(result.records) == 1
    assert result.records[0].metadata["kind"] == "video"


def test_rejects_invalid_bvid() -> None:
    with pytest.raises(ConfigurationError, match="BV"):
        BilibiliAdapter(FakeHttp()).collect(bvid="invalid")


def test_api_error_is_reported() -> None:
    with pytest.raises(RemoteResponseError, match="not found"):
        BilibiliAdapter(FakeHttp(view={"code": -404, "message": "not found"})).collect(
            bvid="BV1xx411c7mD"
        )


def test_malformed_xml_is_reported() -> None:
    with pytest.raises(ParseError, match="XML"):
        BilibiliAdapter(FakeHttp(danmaku="<i>")).collect(bvid="BV1xx411c7mD")
