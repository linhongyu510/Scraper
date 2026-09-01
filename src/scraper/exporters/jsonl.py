"""UTF-8 JSON Lines exporter."""

from collections.abc import Iterable
from pathlib import Path

from scraper.exceptions import ExportError
from scraper.models import Record


def export_jsonl(records: Iterable[Record], output: Path) -> None:
    """Write one normalized JSON object per line."""
    try:
        with output.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(record.model_dump_json())
                handle.write("\n")
    except (OSError, TypeError, ValueError) as exc:
        raise ExportError(f"Unable to write JSONL file {output}: {exc}") from exc
