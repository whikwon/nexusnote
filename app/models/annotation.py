from uuid import uuid4

from odmantic import Field

from app.db.base_class import Base


class Annotation(Base):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_field=True)
    file_id: str
    page_number: int
    comment: str | None
    # frontend 정보 관리가 어떻게 되는지 확인해서 정의하기, rect로 반환해주려나?
