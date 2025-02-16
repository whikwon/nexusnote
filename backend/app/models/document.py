from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from odmantic import Field, Model


class Document(Model):
    # Unique identifier for the file, assigned at upload time (immutable).
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    name: str  # User-visible name of the file, which can be updated or changed on the frontend.
    path: str  # Relative path to the file within the storage directory.
    metadata: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
