from datetime import datetime, timezone
from uuid import uuid4

from odmantic import Field, Model


class Document(Model):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    name: str
    path: str  # Path to the file in storage
    content_type: str = "application/pdf"
    metadata: dict | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
