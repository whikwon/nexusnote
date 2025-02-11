
from langchain_core.documents import Document as langchain_Document
from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    file_id: str
    section_hierarchy: dict[str, str]
    chunk_id: int
    block_ids: list[str]


class Chunk(langchain_Document):
    pass
