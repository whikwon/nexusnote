from typing import Dict, List

from langchain_core.documents import Document as langchain_Document
from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    file_id: str
    section_hierarchy: Dict[str, str]
    chunk_id: int
    block_ids: List[str]


class Chunk(langchain_Document):
    pass
