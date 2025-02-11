
from pydantic import BaseModel


class Annotation(BaseModel):
    file_id: str
    page_number: int
    comment: str | None
    # 위치 정보 추가하기
