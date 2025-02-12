from beanie import Document


class Annotation(Document):
    file_id: str
    page_number: int
    comment: str | None
    # frontend 정보 관리가 어떻게 되는지 확인해서 정의하기, rect로 반환해주려나?
