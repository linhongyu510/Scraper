"""Shared domain models."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, JsonValue


class Record(BaseModel):
    """A normalized public-data record."""

    source: str = Field(min_length=1)
    id: str = Field(min_length=1)
    title: str = ""
    url: HttpUrl
    content: str = ""
    author: str = ""
    published_at: datetime | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class CollectionResult(BaseModel):
    """Records and recoverable item-level errors from one collection."""

    records: list[Record] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
