from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    name: str
    content: str  # base64 encoded


class DocumentUpdate(BaseModel):
    name: str = None
    metadata: dict[str, Any] | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentBase(BaseModel):
    # Unique identifier for the file
    id: str
    name: str  # User-visible name of the file, which can be updated or changed on the frontend.
    path: str  # Relative path to the file within the storage directory.
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
