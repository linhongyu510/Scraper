import pytest
from pydantic import HttpUrl

from scraper.analysis.frequency import record_frequency, word_frequency
from scraper.analysis.wordcloud import generate_wordcloud
from scraper.exceptions import ConfigurationError
from scraper.models import Record


def test_frequency_filters_stopwords() -> None:
    rows = word_frequency(["保护海洋 保护地球", "保护海洋"], stopwords={"保护"})

    assert rows[0] == ("海洋", 2)


def test_frequency_honors_top_and_record_field() -> None:
    records = [
        Record(
            source="test",
            id="1",
            title="alpha beta beta",
            url=HttpUrl("https://example.com/1"),
            content="ignored",
        )
    ]

    assert record_frequency(records, field="title", top=1) == [("beta", 2)]


def test_wordcloud_rejects_missing_explicit_font(tmp_path) -> None:
    with pytest.raises(ConfigurationError, match="font"):
        generate_wordcloud(
            [("海洋", 2)],
            tmp_path / "cloud.png",
            font_path=tmp_path / "missing.ttf",
        )
