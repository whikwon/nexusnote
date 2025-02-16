
from pydantic import BaseModel

from app.models import Block


class RAGRequest(BaseModel):
    file_id: str
    question: str
    k: int = 5


class RAGResponse(BaseModel):
    status: str
    response: str
    question: str | None = None
    answer: int | None = None
    section: list[Block] = None
