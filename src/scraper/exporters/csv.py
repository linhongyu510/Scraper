"""CSV exporter with a stable schema."""

import csv
import json
from collections.abc import Iterable
from pathlib import Path

from scraper.exceptions import ExportError
from scraper.models import Record

CSV_FIELDS = [
    "source",
    "id",
    "title",
    "url",
    "content",
    "author",
    "published_at",
    "metadata",
]


def export_csv(records: Iterable[Record], output: Path) -> None:
    """Write records with deterministic columns and JSON metadata."""
    try:
        with output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "source": record.source,
                        "id": record.id,
                        "title": record.title,
                        "url": str(record.url),
                        "content": record.content,
                        "author": record.author,
                        "published_at": (
                            record.published_at.isoformat() if record.published_at else ""
                        ),
                        "metadata": json.dumps(
                            record.metadata,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    }
                )
    except (OSError, TypeError, ValueError, csv.Error) as exc:
        raise ExportError(f"Unable to write CSV file {output}: {exc}") from exc
