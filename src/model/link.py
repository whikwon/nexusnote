from typing import Tuple

from pydantic import BaseModel

from .concept_node import ConceptNode


class Link(BaseModel):
    nodes: Tuple[ConceptNode, ConceptNode]
    relationship: str
