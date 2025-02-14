from typing import List

from pydantic import BaseModel


class ConceptCreate(BaseModel):
    comment: str
    annotation_id: List[str] | None


class ConceptUpdate(BaseModel):
    concept_id: str
    comment: str
    annotation_id: List[str] | None
