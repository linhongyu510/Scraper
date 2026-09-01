from pathlib import Path

import pytest

from scraper.adapters.web import WebAdapter
from scraper.exceptions import ParseError

FIXTURES = Path(__file__).parents[1] / "fixtures"


class FakeHttp:
    def get_text(self, _url: str, **_kwargs: object) -> str:
        return (FIXTURES / "page.html").read_text()


def test_web_resolves_relative_links() -> None:
    result = WebAdapter(FakeHttp()).collect(
        url="https://example.com/blog/",
        item="article",
        title="h2",
        content="p",
        link="a",
    )

    assert str(result.records[0].url) == "https://example.com/post-1"
    assert result.records[0].content == "Static page content."


def test_web_requires_matching_items() -> None:
    with pytest.raises(ParseError, match="matched no items"):
        WebAdapter(FakeHttp()).collect(
            url="https://example.com/blog/",
            item=".missing",
            title="h2",
            content="p",
            link="a",
        )
