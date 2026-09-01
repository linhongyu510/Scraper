from pathlib import Path

from scraper.adapters.rss import RssAdapter

FIXTURES = Path(__file__).parents[1] / "fixtures"


class FakeHttp:
    def get_text(self, _url: str, **_kwargs: object) -> str:
        return (FIXTURES / "feed.xml").read_text()


def test_rss_uses_guid_as_id() -> None:
    result = RssAdapter(FakeHttp()).collect(url="https://example.com/feed.xml")

    assert result.records[0].id == "post-1"
    assert result.records[0].title == "First post"
    assert result.records[0].source == "rss"


def test_rss_missing_id_uses_stable_fallback() -> None:
    class MinimalHttp:
        def get_text(self, _url: str, **_kwargs: object) -> str:
            return "<rss><channel><item><title>Only title</title></item></channel></rss>"

    first = RssAdapter(MinimalHttp()).collect(url="https://example.com/feed").records[0]
    second = RssAdapter(MinimalHttp()).collect(url="https://example.com/feed").records[0]

    assert first.id == second.id
