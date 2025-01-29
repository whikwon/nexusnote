import io
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import uuid4

import fitz
from langchain_core.documents import Document as langchain_Document
from PIL import Image
from pydantic import BaseModel, Field

from src.pdf_helper.layout_extractor import PaddleX17Cls, PaddleXBox
from src.utils import pil_to_base64


class ChunkMetaData(BaseModel):
    start_page: int
    end_page: int
    file_name: str  # change the file name to a UUID when uploading
    created_at: str
    updated_at: str


class PaddleXBoxContent(BaseModel):
    page_number: int
    bbox: List[float]
    cls_id: PaddleX17Cls
    text: Optional[str] = None
    image: Optional[str] = None


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


class EnrichedPaddleXBoxContent(PaddleXBoxContent):
    id: str = Field(default_factory=lambda: str(uuid4()))
    references_to: List[Reference] = []
    referenced_by: List[Reference] = []


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

    return PaddleXBoxContent(**result)


def chunk_layout_contents(
    content_list: List[EnrichedPaddleXBoxContent],
    max_boxes_per_chunk: int = 20,
    overlap_boxes: int = 3,
) -> List[langchain_Document]:
    """
    Creates chunks from layout-extracted PDF content, preserving layout structure
    and UUIDs for traceability. Chunks are created based on number of content boxes
    rather than character count.

    Args:
        content_list (List[EnrichedContent]): List of enriched content with UUIDs
        max_boxes_per_chunk (int): Maximum number of content boxes per chunk
        overlap_boxes (int): Number of content boxes to overlap between chunks
    Returns:
        List[langchain_Document]: List of document chunks with metadata including UUIDs
    """
    chunks = []
    current_boxes: List[EnrichedPaddleXBoxContent] = []
    current_pages: Set[int] = set()
    current_uuids: Set[str] = set()

    # Sort content by page number and vertical position (bbox[1])
    sorted_contents = sorted(content_list, key=lambda x: (x.page_number, x.bbox[1]))

    def create_chunk_text(boxes: List[EnrichedPaddleXBoxContent]) -> str:
        """Helper function to create chunk text from content boxes"""
        chunk_parts = []
        for box in boxes:
            if box.image is not None:
                chunk_parts.append(
                    f'<{box.cls_id.name} id="{box.id}">{box.image}</{box.cls_id.name}>'
                )
            elif box.text:
                text = box.text.strip()
                if text:
                    chunk_parts.append(
                        f'<{box.cls_id.name} id="{box.id}">{text}</{box.cls_id.name}>'
                    )
        return "\n".join(chunk_parts)

    def create_chunk_document(
        boxes: List[EnrichedPaddleXBoxContent],
    ) -> langchain_Document:
        """Helper function to create a document with consistent metadata"""
        pages = {box.page_number for box in boxes}
        uuids = {box.id for box in boxes}

        # Get all references for the boxes in this chunk
        references: Dict[str, List[str]] = {"references_to": [], "referenced_by": []}
        for box in boxes:
            # Add outgoing references
            references["references_to"].extend(
                [ref.target_id for ref in box.references_to]
            )
            # Add incoming references
            references["referenced_by"].extend(
                [ref.target_id for ref in box.referenced_by]
            )

        return langchain_Document(
            page_content=create_chunk_text(boxes),
            metadata={
                "page_numbers": sorted(pages),
                "content_uuids": sorted(uuids),
                "references": {
                    "references_to": sorted(set(references["references_to"])),
                    "referenced_by": sorted(set(references["referenced_by"])),
                },
            },
        )

    # Process content boxes into chunks
    for content in sorted_contents:
        current_boxes.append(content)
        current_pages.add(content.page_number)
        current_uuids.add(content.id)

        # Check if we've reached the maximum boxes per chunk
        if len(current_boxes) >= max_boxes_per_chunk:
            # Create chunk
            chunks.append(create_chunk_document(current_boxes))

            # Keep overlap boxes for next chunk
            current_boxes = current_boxes[-overlap_boxes:]
            current_pages = {box.page_number for box in current_boxes}
            current_uuids = {box.id for box in current_boxes}

    # Add final chunk if there are remaining boxes
    if current_boxes:
        chunks.append(create_chunk_document(current_boxes))

    # Post-process chunks to ensure proper connection of references
    for i, chunk in enumerate(chunks):
        # Add references to overlapping content in adjacent chunks
        if i > 0:  # Not the first chunk
            prev_chunk_uuids = set(chunks[i - 1].metadata["content_uuids"])
            chunk.metadata["references"]["prev_chunk_uuids"] = sorted(
                prev_chunk_uuids & set(chunk.metadata["content_uuids"])
            )

        if i < len(chunks) - 1:  # Not the last chunk
            next_chunk_uuids = set(chunks[i + 1].metadata["content_uuids"])
            chunk.metadata["references"]["next_chunk_uuids"] = sorted(
                next_chunk_uuids & set(chunk.metadata["content_uuids"])
            )

    return chunks
