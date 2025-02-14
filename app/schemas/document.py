from pydantic import BaseModel


class DocumentCreate(BaseModel):
    name: str
    content: str  # base64 encoded


class DocumentUpdate(BaseModel):
    name: str
