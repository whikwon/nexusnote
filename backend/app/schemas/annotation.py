from datetime import datetime, timezone

from pydantic import BaseModel, Field


class AnnotationCreate(BaseModel):
    file_id: str
    page_number: int
    comment: str | None = None
    # 범위


class AnnotationUpdate(BaseModel):
    id: str
    comment: str
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc))
    # 범위


class AnnotationBase(BaseModel):
    id: str
    file_id: str
    page_number: int
    comment: str | None = None
    created_at: datetime
    updated_at: datetime
    # 범위
