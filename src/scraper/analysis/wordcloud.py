"""Optional word-cloud rendering."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scraper.exceptions import ConfigurationError, ExportError

COMMON_CJK_FONTS = (
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
    Path("C:/Windows/Fonts/msyh.ttc"),
)


def find_cjk_font() -> Path | None:
    """Return the first known CJK font available on this system."""
    return next((path for path in COMMON_CJK_FONTS if path.is_file()), None)


def generate_wordcloud(
    frequencies: Iterable[tuple[str, int]],
    output: Path,
    *,
    font_path: Path | None = None,
    width: int = 1200,
    height: int = 800,
) -> Path:
    """Render frequencies to PNG using an explicit or discovered CJK font."""
    selected_font = font_path or find_cjk_font()
    if selected_font is None or not selected_font.is_file():
        raise ConfigurationError(
            "A Chinese-capable font is required; install a CJK font or pass --font-path"
        )
    values = dict(frequencies)
    if not values:
        raise ConfigurationError("Cannot generate a word cloud from empty frequencies")

    try:
        from wordcloud import WordCloud  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ConfigurationError(
            'Word-cloud support is optional; install it with pip install ".[analysis]"'
        ) from exc

    try:
        cloud = WordCloud(
            font_path=str(selected_font),
            width=width,
            height=height,
            background_color="white",
        ).generate_from_frequencies(values)
        cloud.to_file(str(output))
    except (OSError, ValueError) as exc:
        raise ExportError(f"Unable to create word cloud {output}: {exc}") from exc
    return output
