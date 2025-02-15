from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DocumentCreate(BaseModel):
    name: str
    content: str  # base64 encoded


class DocumentUpdate(BaseModel):
    name: str = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentBase(BaseModel):
    # Unique identifier for the file
    id: str
    name: str  # User-visible name of the file, which can be updated or changed on the frontend.
    path: str  # Relative path to the file within the storage directory.
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
