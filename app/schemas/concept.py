from typing import List

from pydantic import BaseModel


class ConceptCreate(BaseModel):
    name: str
    comment: str
    annotation_ids: List[str] | None


class ConceptUpdate(BaseModel):
    name: str
    comment: str
    annotation_ids: List[str] | None
