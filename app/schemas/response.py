from typing import List, Optional

from pydantic import BaseModel

from app.models.block import Block


class RAGResponse(BaseModel):
    status: str
    response: str
    question: Optional[str] = None
    answer: Optional[int] = None
    section: List[Block] = None


class UploadDocumentResponse(BaseModel):
    status: str
    file_id: str
    message: Optional[str] = None


class ProcessDocumentResponse(BaseModel):
    status: str
    file_id: Optional[str] = None
    num_chunks: Optional[int] = None
    message: Optional[str] = None
