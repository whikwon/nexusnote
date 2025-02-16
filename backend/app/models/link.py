from datetime import datetime, timezone
from uuid import uuid4

from odmantic import Field, Model


class Link(Model):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    concept_ids: list[str]
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
