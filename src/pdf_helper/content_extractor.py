import io
from enum import Enum
from typing import Dict, List, Optional, Set
from uuid import uuid4

import fitz
from langchain_core.documents import Document as langchain_Document
from PIL import Image
from pydantic import BaseModel, Field

from src.pdf_helper.layout_extractor import PaddleX17Cls, PaddleXBox
from src.utils.image import pil_to_base64


class ChunkMetaData(BaseModel):
    start_page: int
    end_page: int
    file_name: str  # change the file name to a UUID when uploading
    created_at: str
    updated_at: str


class FontData(BaseModel, frozen=True):
    name: str
    size: float


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


def chunk_layout_contents(
    content_list: List[PaddleXBoxContent],
    content_filter_func=None,
    max_chunk_size: int = 5_000,  # Maximum characters per chunk
    overlap_boxes: int = 1,
) -> List[langchain_Document]:
    """
    Creates chunks from layout-extracted PDF content, preserving layout structure
    and UUIDs for traceability. Chunks are created based on character count
    rather than number of boxes.

    Args:
        content_list (List[EnrichedContent]): List of enriched content with UUIDs
        content_filter_func: Optional function to filter content
        max_chunk_size (int): Maximum number of characters per chunk
        overlap_boxes (int): Number of content boxes to overlap between chunks

    Returns:
        List[langchain_Document]: List of document chunks with metadata including UUIDs
    """
    chunks = []
    current_boxes: List[PaddleXBoxContent] = []
    current_size: int = 0
    current_pages: Set[int] = set()
    current_uuids: Set[str] = set()

    if content_filter_func is not None:
        content_list = [
            content for content in content_list if content_filter_func(content)
        ]

    # Sort content by page number and vertical position (bbox[1])
    sorted_contents = sorted(content_list, key=lambda x: (x.page_number, x.bbox[1]))

    def get_box_size(box: PaddleXBoxContent) -> int:
        if box.image is not None:
            # Apply a weight factor to image size since base64 is verbose
            # Decode base64 to get actual image size in bytes
            import base64

            image_bytes = base64.b64decode(box.image)
            return len(image_bytes) // 4  # Adjust weight factor as needed
        return len(box.text.strip()) if box.text else 0

    def create_chunk_text(boxes: List[PaddleXBoxContent]) -> str:
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
        boxes: List[PaddleXBoxContent],
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
        box_size = get_box_size(content)

        # If adding this box would exceed the chunk size, create a new chunk
        if current_size + box_size > max_chunk_size and current_boxes:
            # Create chunk
            chunks.append(create_chunk_document(current_boxes))

            # Keep overlap boxes for next chunk
            if overlap_boxes > 0:
                current_boxes = current_boxes[-overlap_boxes:]
                current_size = sum(get_box_size(box) for box in current_boxes)
                current_pages = {box.page_number for box in current_boxes}
                current_uuids = {box.id for box in current_boxes}
            else:
                current_boxes = []
                current_size = 0
                current_pages = set()
                current_uuids = set()

        # Add current content
        current_boxes.append(content)
        current_size += box_size
        current_pages.add(content.page_number)
        current_uuids.add(content.id)

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
