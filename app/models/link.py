from typing import List
from uuid import uuid4

from odmantic import Field

from app.db.base_class import Base


class Link(Base):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    concept_ids: List[str]
