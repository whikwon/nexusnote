from pydantic import BaseModel


class PDFProcessRequest(BaseModel):
    file_id: str
    file_name: str
