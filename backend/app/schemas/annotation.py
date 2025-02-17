from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Optional


class HighlightArea(BaseModel):
    height: float
    left: float
    pageIndex: int
    top: float
    width: float


class AnnotationCreate(BaseModel):
    file_id: str
    comment: str
    quote: str
    highlight_areas: List[HighlightArea]


class AnnotationUpdate(BaseModel):
    id: str
    comment: str = None
    highlight_areas: Optional[List[HighlightArea]] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnnotationBase(BaseModel):
    id: str
    file_id: str
    highlight_areas: List[HighlightArea]
    quote: str
    comment: str
    created_at: datetime
    updated_at: datetime
