from datetime import datetime, timezone
from uuid import uuid4

from odmantic import Field, Model


class Concept(Model):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    name: str
    comment: str
    annotation_ids: list[str] = Field(default_factory=list)
    connected_concepts: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
