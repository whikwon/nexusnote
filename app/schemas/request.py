from pydantic import BaseModel


class DocumentProcessRequest(BaseModel):
    file_id: str


class DocumentUploadRequest(BaseModel):
    file_name: str
    content: str  # base64 encoded


class RAGRequest(BaseModel):
    file_id: str
    question: str
    k: int = 5
