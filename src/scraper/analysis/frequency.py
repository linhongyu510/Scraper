"""Unicode-aware word frequency analysis."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from typing import Literal

import jieba  # type: ignore[import-untyped]

from scraper.models import Record

RecordField = Literal["title", "content", "author"]
WORD_PATTERN = re.compile(r"[\w\u3400-\u9fff]+", re.UNICODE)


def word_frequency(
    texts: Iterable[str],
    *,
    stopwords: set[str] | None = None,
    min_length: int = 1,
    top: int = 50,
) -> list[tuple[str, int]]:
    """Return deterministic token counts sorted by count and then token."""
    blocked = stopwords or set()
    counter: Counter[str] = Counter()
    for text in texts:
        for token in jieba.cut(text):
            normalized = token.strip().lower()
            if (
                len(normalized) >= min_length
                and normalized not in blocked
                and WORD_PATTERN.fullmatch(normalized)
            ):
                counter[normalized] += 1
    return sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))[:top]


def record_frequency(
    records: Iterable[Record],
    *,
    field: RecordField = "content",
    stopwords: set[str] | None = None,
    min_length: int = 1,
    top: int = 50,
) -> list[tuple[str, int]]:
    """Count words in one normalized record field."""
    return word_frequency(
        (getattr(record, field) for record in records),
        stopwords=stopwords,
        min_length=min_length,
        top=top,
    )
