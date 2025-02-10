from typing import List, Optional

from pydantic import BaseModel

from .annotation import Annotation


class ConceptNode(BaseModel):
    node_id: str
    annotations: List[Annotation]
    comment: Optional[str]
    links: List[str]
