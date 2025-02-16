from typing import List
from uuid import uuid4

from odmantic import Field, Model


class Link(Model):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    concept_ids: List[str]
