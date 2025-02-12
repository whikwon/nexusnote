from uuid import uuid4

from beanie import Document
from pydantic import Field, conlist


class ConceptLink(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    concept_ids: conlist(str, min_length=2, max_length=2)
