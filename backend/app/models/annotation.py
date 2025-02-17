from datetime import datetime, timezone
from uuid import uuid4
from typing import List
from odmantic import Field, Model, EmbeddedModel


class HighlightArea(EmbeddedModel):
    height: float
    left: float
    pageIndex: int
    top: float
    width: float


class Annotation(Model):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    file_id: str
    highlight_areas: List[HighlightArea] = Field(default_factory=list)
    quote: str
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
