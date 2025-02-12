from typing import List

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


class CreateAnnotationRequest(BaseModel):
    file_id: str
    page_number: int
    comment: str
    # 범위


class DeleteAnnotationRequest(BaseModel):
    annotation_id: str


class UpdateAnnotationRequest(BaseModel):
    annotation_id: str
    comment: str
    # 범위


class CreateConceptRequest(BaseModel):
    comment: str
    annotation_id: List[str] | None


class DeleteConceptRequest(BaseModel):
    concept_id: str


class UpdateConceptRequest(BaseModel):
    concept_id: str
    comment: str
    annotation_id: List[str] | None
