from pydantic import BaseModel


class AnnotationCreate(BaseModel):
    file_id: str
    page_number: int
    comment: str | None = None
    # 범위


class AnnotationUpdate(BaseModel):
    id: str
    comment: str
    # 범위


class AnnotationBase(BaseModel):
    id: str
    file_id: str
    page_number: int
    comment: str | None = None
    # 범위
