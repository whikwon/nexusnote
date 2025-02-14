from typing import List

from pydantic import BaseModel, conlist


class GetDocumentRequest(BaseModel):
    file_id: str


class ProcessDocumentRequest(BaseModel):
    file_id: str


class UploadDocumentRequest(BaseModel):
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


# comment, 범위 모두 수정할 수 있도록 구현
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


class CreateConceptLinkRequest(BaseModel):
    concept_ids: conlist(str, min_length=2, max_length=2)


class DeleteConceptLinkRequest(BaseModel):
    link_id: str
