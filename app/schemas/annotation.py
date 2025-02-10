from typing import Optional

from pydantic import BaseModel


class Annotation(BaseModel):
    file_id: str
    page_number: int
    comment: Optional[str]
