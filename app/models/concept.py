from typing import List
from uuid import uuid4

from odmantic import Field, Model


class Concept(Model):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    name: str
    comment: str
    annotation_ids: List[str]
