from pydantic import BaseModel


class AnnotationCreate(BaseModel):
    file_id: str
    page_number: int
    comment: str
    # 범위


class AnnotationUpdate(BaseModel):
    comment: str
    # 범위
