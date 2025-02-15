from typing import List

from pydantic import BaseModel, Field


class ConceptCreate(BaseModel):
    name: str
    comment: str
    annotation_ids: List[str] = Field(default_factory=list)


class ConceptUpdate(BaseModel):
    name: str
    comment: str
    annotation_ids: List[str] = Field(default_factory=list)


class ConceptBase(BaseModel):
    id: str
    name: str
    comment: str
    annotation_ids: List[str] = Field(default_factory=list)
