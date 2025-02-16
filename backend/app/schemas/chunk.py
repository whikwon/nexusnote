from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    file_id: str
    section_hierarchy: dict[str, str]
    chunk_id: int
    block_ids: list[str]
    embedding_model: str | None = None
