from typing import Optional

from pydantic import BaseModel


class RAGResponse(BaseModel):
    status: str
    response: str
    question: Optional[str] = None
    documents_retrieved: Optional[int] = None


class UploadDocumentResponse(BaseModel):
    status: str
    file_id: str
    message: Optional[str] = None


class ProcessDocumentResponse(BaseModel):
    status: str
    file_id: Optional[str] = None
    num_chunks: Optional[int] = None
    message: Optional[str] = None
