from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ConceptCreate(BaseModel):
    name: str
    comment: str
    annotation_ids: list[str] = Field(default_factory=list)


class ConceptUpdate(BaseModel):
    id: str
    name: str
    comment: str
    annotation_ids: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConceptBase(BaseModel):
    id: str
    name: str
    comment: str
    annotation_ids: list[str] = Field(default_factory=list)
    linked_concept_ids: list[str] = Field(default_factory=list)
