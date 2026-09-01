"""Load normalized records from local files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pydantic import HttpUrl, ValidationError

from scraper.exceptions import ConfigurationError, ParseError
from scraper.models import Record


def load_records(path: Path) -> list[Record]:
    """Load JSONL, CSV, or line-oriented text records."""
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return _load_jsonl(path)
    if suffix == ".csv":
        return _load_csv(path)
    if suffix == ".txt":
        return _load_text(path)
    raise ConfigurationError("Input must have a .jsonl, .csv, or .txt extension")


def _load_jsonl(path: Path) -> list[Record]:
    records: list[Record] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    records.append(Record.model_validate_json(line))
                except (ValidationError, ValueError) as exc:
                    raise ParseError(f"{path.name}:{line_number}: invalid record: {exc}") from exc
    except OSError as exc:
        raise ParseError(f"Unable to read {path}: {exc}") from exc
    return records


def _load_csv(path: Path) -> list[Record]:
    records: list[Record] = []
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            for line_number, row in enumerate(csv.DictReader(handle), start=2):
                try:
                    values: dict[str, object] = dict(row)
                    values["metadata"] = json.loads(row.get("metadata") or "{}")
                    values["published_at"] = row.get("published_at") or None
                    records.append(Record.model_validate(values))
                except (ValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
                    raise ParseError(f"{path.name}:{line_number}: invalid record: {exc}") from exc
    except (OSError, csv.Error) as exc:
        raise ParseError(f"Unable to read {path}: {exc}") from exc
    return records


def _load_text(path: Path) -> list[Record]:
    records: list[Record] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                content = line.strip()
                if not content:
                    continue
                records.append(
                    Record(
                        source="text",
                        id=f"{path.name}:{line_number}",
                        url=HttpUrl(f"https://local.invalid/{path.name}#L{line_number}"),
                        content=content,
                        metadata={"kind": "text-line", "line": line_number},
                    )
                )
    except OSError as exc:
        raise ParseError(f"Unable to read {path}: {exc}") from exc
    return records
