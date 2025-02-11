
from pydantic import BaseModel

from .concept_node import ConceptNode


class Link(BaseModel):
    nodes: tuple[ConceptNode, ConceptNode]
    relationship: str
