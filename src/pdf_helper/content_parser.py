import io
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import uuid4

import fitz
from langchain_core.documents import Document as langchain_Document
from PIL import Image
from pydantic import BaseModel, Field

from src.pdf_helper.layout_parser import PaddleX17Cls, PaddleXBox
from src.utils.image import pil_to_base64


class ChunkMetaData(BaseModel):
    start_page: int
    end_page: int
    file_name: str  # change the file name to a UUID when uploading
    created_at: str
    updated_at: str


class FontData(BaseModel):
    name: str
    size: float

    class Config:
        frozen = True


class TextData(BaseModel):
    content: str
    fonts: List[FontData]


class PaddleXBoxContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_id: str
    page_number: int
    bbox: List[float]
    cls_id: PaddleX17Cls
    text: Optional[TextData] = None
    image: Optional[str] = None

    class Config:
        json_encoders: {PaddleX17Cls: lambda v: v.value}


class ReferenceType(str, Enum):
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    SECTION = "section"
    ALGORITHM = "algorithm"


class Reference(BaseModel):
    target_id: str
    type: ReferenceType
    text: str

    class Config:
        json_encoders: {ReferenceType: lambda v: v.value}


def parse_box_contents(
    page: fitz.Page, box: PaddleXBox, w_scale: float, h_scale: float, file_id: str
) -> dict:
    cls_id = box.cls_id
    bbox = [
        box.coordinate[0] * w_scale,
        box.coordinate[1] * h_scale,
        box.coordinate[2] * w_scale,
        box.coordinate[3] * h_scale,
    ]
    result = {
        "page_number": page.number + 1,
        "bbox": bbox,
        "cls_id": cls_id,
        "file_id": file_id,
    }

    if cls_id in [
        PaddleX17Cls.picture,
        PaddleX17Cls.table,
        PaddleX17Cls.algorithm,
        PaddleX17Cls.formula,
    ]:
        pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
        png_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(png_bytes))
        cropped_img = img.crop(bbox)
        base64_string = pil_to_base64(cropped_img)
        result.update(
            {
                "image": base64_string,
            }
        )
    else:
        text_parts = []
        fonts = set()
        blocks = page.get_text("dict", clip=bbox)
        for block in blocks["blocks"]:
            block_text = []
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    line_text += span["text"]
                    fonts.add(FontData(name=span["font"], size=span["size"]))
                block_text.append(line_text)
            text_parts.append(" ".join(block_text))
        text = "\n\n".join(text_parts)
        result.update({"text": {"content": text, "fonts": list(fonts)}})

    return PaddleXBoxContent(**result)
