from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from beanie import Document as BeanieDocument
from pydantic import Field


class Document(BeanieDocument):
    id: str = Field(
        default_factory=lambda: str(uuid4())
    )  # Unique identifier for the file, assigned at upload time (immutable).
    name: str  # User-visible name of the file, which can be updated or changed on the frontend.
    path: str  # Relative path to the file within the storage directory.
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
