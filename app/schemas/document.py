from pydantic import BaseModel


class DocumentCreate(BaseModel):
    file_name: str
    content: str  # base64 encoded


class DocumentUpdate(BaseModel):
    file_id: str
    file_name: str
