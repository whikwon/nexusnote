from typing import List
from uuid import uuid4

from odmantic import Field

from app.db.base_class import Base


class Concept(Base):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    name: str
    comment: str
    annotation_ids: List[str]
