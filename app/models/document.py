from datetime import datetime, timezone
from typing import Any, Dict, Optional

from beanie import Document as BeanieDocument
from pydantic import Field


class Document(BeanieDocument):
    file_id: str  # Unique identifier for the file, assigned at upload time (immutable).
    file_name: str  # User-visible name of the file, which can be updated or changed on the frontend.
    file_path: str  # Relative path to the file within the storage directory.
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
