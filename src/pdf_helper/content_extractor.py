import base64
import io from typing import List, Optional

import fitz
from gmft.detectors.common import CroppedTable
from langchain_core.vectorstores.base import Document as langchain_Document
from PIL import Image
from pydantic import BaseModel

from src.pdf_helper.layout_extractor import PaddleX17Cls, PaddleXBox
from src.utils import pil_to_base64


def _is_within_table(text_block, table_bboxes):
    """
    Checks if a text block is within a table.
    """
    block_bbox = text_block["bbox"]
    for table_bbox in table_bboxes:
        # Check if block overlaps with any table bbox
        if (
            block_bbox[0] < table_bbox[2]
            and block_bbox[2] > table_bbox[0]
            and block_bbox[1] < table_bbox[3]
            and block_bbox[3] > table_bbox[1]
        ):
            return True
    return False


class ChunkMetaData(BaseModel):
    start_page: int
    end_page: int
    file_name: str  # change the file name to a UUID when uploading
    created_at: str
    updated_at: str


def chunk_pages(
    doc: fitz.Document,
    pages: List[int] = None,
    tables_per_page: List[CroppedTable] = None,
    chunk_size=10_000,
    overlap=200,
) -> List[langchain_Document]:
    """
    Extracts text chunks from a document, excluding text within tables.
    Table images are included in the chunks.
    Images from tables are also included in the chunks.

    Args:
        pages (list): A list of PyMuPDF pages.
        tables_per_page (list): A list of tables detected on each page.
        chunk_size (int): The maximum size of each chunk.
        overlap (int): The number of characters to overlap between chunks.

    Returns:
        list: A list of text chunks.
    """
    if tables_per_page is None:
        tables_per_page = [None] * len(pages)
    else:
        if pages is not None:
            assert len(pages) == len(tables_per_page)
        else:
            assert len(tables_per_page) == doc.page_count

    chunks = []
    current_chunk = ""
    current_size = 0
    overlap_buffer = ""

    for page, tables in zip(pages, tables_per_page):
        table_bboxes = [table.bbox for table in tables]
        blocks = page.get_text("dict")["blocks"]
        blocks_and_tables = blocks + tables
        blocks_and_tables.sort(
            key=lambda x: x["bbox"][1] if isinstance(x, dict) else x.bbox[1]
        )

        for block_or_table in blocks_and_tables:
            if isinstance(block_or_table, CroppedTable):
                if block_or_table.confidence_score < 0.99:
                    continue

                img_bytes = io.BytesIO()
                block_or_table.image().save(img_bytes, format="PNG")
                b64_image = base64.b64encode(img_bytes.getvalue()).decode()
                image_chunk = f" <table_image>{b64_image}</table_image> "

                if current_size + len(image_chunk) > chunk_size:
                    chunks.append(langchain_Document(page_content=current_chunk))
                    current_chunk = image_chunk  # Don't overlap images
                    current_size = len(image_chunk)
                else:
                    current_chunk += image_chunk
                    current_size += len(image_chunk)
            else:
                if _is_within_table(block_or_table, table_bboxes):
                    continue
                if block_or_table["type"] == 1:
                    b64_image = base64.b64encode(block_or_table["image"]).decode()
                    image_chunk = f" <figure_image>{b64_image}</figure_image> "

                    if current_size + len(image_chunk) > chunk_size:
                        chunks.append(langchain_Document(page_content=current_chunk))
                        current_chunk = image_chunk  # Don't overlap images
                        current_size = len(image_chunk)
                    else:
                        current_chunk += image_chunk
                        current_size += len(image_chunk)
                else:
                    for line in block_or_table["lines"]:
                        text = line["spans"][0]["text"].strip()
                        if not text:
                            continue

                        text = f" {text} "
                        if current_size + len(text) > chunk_size:
                            chunks.append(
                                langchain_Document(page_content=current_chunk)
                            )
                            overlap_buffer = (
                                current_chunk[-overlap:]
                                if len(current_chunk) > overlap
                                else current_chunk
                            )
                            current_chunk = overlap_buffer + text
                            current_size = len(current_chunk)
                        else:
                            current_chunk += text
                            current_size += len(text)

    if current_chunk:
        chunks.append(langchain_Document(page_content=current_chunk))

    return chunks


class PaddleXBoxContent(BaseModel):
    page_number: int
    bbox: List[float]
    cls_id: PaddleX17Cls
    text: Optional[str] = None
    image: Optional[str] = None


def parse_box_contents(
    page: fitz.Page, box: PaddleXBox, w_scale: float, h_scale: float
) -> dict:
    cls_id = box.cls_id
    bbox = [
        box.coordinate[0] * w_scale,
        box.coordinate[1] * h_scale,
        box.coordinate[2] * w_scale,
        box.coordinate[3] * h_scale,
    ]
    result = {
        "page_number": page.number,
        "bbox": bbox,
        "cls_id": cls_id,
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
        blocks = page.get_text("dict", clip=bbox)
        for block in blocks["blocks"]:
            block_text = []
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    line_text += span["text"]
                block_text.append(line_text)
            text_parts.append(" ".join(block_text))
        text = "\n\n".join(text_parts)
        result.update({"text": text})

    return result
