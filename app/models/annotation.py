from uuid import uuid4

from beanie import Document
from pydantic import Field


class Annotation(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_id: str
    page_number: int
    comment: str | None
    # frontend 정보 관리가 어떻게 되는지 확인해서 정의하기, rect로 반환해주려나?
