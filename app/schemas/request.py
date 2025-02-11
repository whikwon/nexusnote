from pydantic import BaseModel


class PDFProcessRequest(BaseModel):
    file_id: str


class PDFAddRequest(BaseModel):
    file_name: str
    content: str  # base64 encoded
