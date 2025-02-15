from typing import List, Optional

from pydantic import BaseModel

from app.models import Block


class RAGRequest(BaseModel):
    file_id: str
    question: str
    k: int = 5


class RAGResponse(BaseModel):
    status: str
    response: str
    question: Optional[str] = None
    answer: Optional[int] = None
    section: List[Block] = None
