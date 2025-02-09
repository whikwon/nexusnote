from typing import List

from pydantic import BaseModel

from .block import Block


class Page(BaseModel):
    file_id: str
    page_number: int
    blocks: List[Block]
