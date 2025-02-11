
from pydantic import BaseModel

from .annotation import Annotation


class ConceptNode(BaseModel):
    node_id: str
    annotations: list[Annotation]
    comment: str | None
    links: list[str]
