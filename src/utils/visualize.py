import random
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Optional

import fitz
from pydantic import BaseModel

from src.pdf_helper.content_extractor import PaddleX17Cls


def get_fixed_colors():
    """Return a predefined color mapping for each content type."""
    return {
        PaddleX17Cls.paragraph_title: (0.2, 0.6, 1.0),  # Light blue
        PaddleX17Cls.picture: (0.9, 0.3, 0.3),  # Coral red
        PaddleX17Cls.text: (0.4, 0.7, 0.4),  # Soft green
        PaddleX17Cls.number: (0.8, 0.4, 0.8),  # Purple
        PaddleX17Cls.abstract: (0.2, 0.5, 0.7),  # Dark blue
        PaddleX17Cls.content: (0.5, 0.5, 0.5),  # Gray
        PaddleX17Cls.chart_title: (1.0, 0.5, 0.0),  # Orange
        PaddleX17Cls.formula: (0.7, 0.2, 0.7),  # Deep purple
        PaddleX17Cls.table: (0.0, 0.6, 0.6),  # Teal
        PaddleX17Cls.table_title: (0.0, 0.7, 0.7),  # Lighter teal
        PaddleX17Cls.reference: (0.6, 0.4, 0.2),  # Brown
        PaddleX17Cls.document_title: (0.1, 0.4, 0.8),  # Royal blue
        PaddleX17Cls.footnote: (0.5, 0.5, 0.3),  # Olive
        PaddleX17Cls.header: (0.3, 0.3, 0.7),  # Navy blue
        PaddleX17Cls.algorithm: (0.8, 0.3, 0.5),  # Rose
        PaddleX17Cls.footer: (0.4, 0.4, 0.4),  # Dark gray
        PaddleX17Cls.seal: (0.7, 0.1, 0.1),  # Dark red
    }


def add_text_to_page(
    page: fitz.Page, point: fitz.Point, text: str, color=(0, 0, 0), size=8
):
    """Add text directly to page instead of using text annotation."""
    page.insert_text(
        point,
        text,
        color=color,
        fontsize=size,
        render_mode=2,  # Makes text appear on top of other content
    )


def visualize_pdf_contents(
    pdf_path: str,
    enriched_content_list: List,
    chunks: Optional[List] = None,
    output_path: str = "visualized_pdf.pdf",
    draw_boxes: bool = True,
    draw_chunks: bool = True,
    draw_references: bool = True,
):
    """
    Create a copy of the original PDF and add annotations for visualization.
    """
    # Create a copy of the original PDF
    shutil.copy2(pdf_path, output_path)

    # Open the copied PDF for annotation
    doc = fitz.open(output_path)

    # Use fixed colors for different classes
    cls_colors = get_fixed_colors()
    chunk_color = (0, 0, 0.8)  # Consistent blue for chunk boundaries

    # Group content by page
    page_content = {}
    for content in enriched_content_list:
        if content.page_number not in page_content:
            page_content[content.page_number] = []
        page_content[content.page_number].append(content)

    # First pass: Create all highlights and store reference target positions
    reference_targets = {}  # Store target positions for linking
    for page_num in range(len(doc)):
        page = doc[page_num]

        if page_num in page_content:
            # Draw individual content boxes
            if draw_boxes:
                for content in page_content[page_num]:
                    rect = fitz.Rect(content.bbox)
                    color = cls_colors[content.cls_id]

                    # Add highlight annotation
                    highlight = page.add_highlight_annot(rect)
                    highlight.set_colors(stroke=color)
                    highlight.set_opacity(0.3)
                    highlight.update()

                    # Add class label directly to page
                    text_point = fitz.Point(rect.x0, rect.y0 - 2)
                    add_text_to_page(
                        page, text_point, f"{content.cls_id.name}", color=color, size=8
                    )

                    # Store reference target position
                    reference_targets[content.id] = {"page": page_num, "rect": rect}

    # Second pass: Add reference links
    if draw_references:
        for page_num in range(len(doc)):
            if page_num not in page_content:
                continue

            page = doc[page_num]

            # Get page dimensions
            for content in page_content[page_num]:
                if not content.references_to or not content.text:
                    continue

                for ref in content.references_to:
                    target = reference_targets.get(ref.target_id)
                    if not target:
                        continue

                    # Find the reference text in the content
                    ref_text = ref.text  # e.g., "Figure 2"
                    text_start = content.text.find(ref_text)
                    if text_start == -1:
                        continue

                    # Calculate the reference text position within the content box
                    text_areas = page.get_text("dict", clip=fitz.Rect(content.bbox))

                    for block in text_areas.get("blocks", []):
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                span_text = span["text"]
                                if ref_text in span_text:
                                    # Create link just for the reference text area
                                    ref_rect = fitz.Rect(span["bbox"])

                                    try:
                                        # Create link annotation with proper coordinates
                                        target_rect = target["rect"]
                                        link = {
                                            "kind": fitz.LINK_GOTO,
                                            "page": target["page"],
                                            "from": ref_rect,
                                            "to": fitz.Point(
                                                target_rect.x0, target_rect.y0
                                            ),
                                        }
                                        page.insert_link(link)

                                        # Add visual indicator for the link
                                        underline = page.add_underline_annot(ref_rect)
                                        underline.set_colors(
                                            stroke=(1, 0, 0)
                                        )  # Red underline
                                        underline.update()

                                    except Exception as e:
                                        print(
                                            f"Error creating link for {ref_text}: {e}"
                                        )

    # Draw chunk boundaries if provided
    if chunks and draw_chunks:
        for chunk_idx, chunk in enumerate(chunks):
            page_numbers = chunk.metadata["page_numbers"]
            content_uuids = set(chunk.metadata["content_uuids"])

            # Find all boxes in this chunk
            chunk_boxes = [
                content
                for content in enriched_content_list
                if content.id in content_uuids
            ]

            # Draw chunk boundary
            for page_num in page_numbers:
                page = doc[page_num]
                page_boxes = [box for box in chunk_boxes if box.page_number == page_num]

                if page_boxes:
                    # Calculate chunk boundary
                    x0 = min(box.bbox[0] for box in page_boxes)
                    y0 = min(box.bbox[1] for box in page_boxes)
                    x1 = max(box.bbox[2] for box in page_boxes)
                    y1 = max(box.bbox[3] for box in page_boxes)

                    # Draw chunk boundary directly on page
                    chunk_rect = fitz.Rect(x0 - 5, y0 - 5, x1 + 5, y1 + 5)
                    page.draw_rect(
                        chunk_rect,
                        color=chunk_color,
                        width=2,
                        dashes=[2, 2],  # Dashed line pattern
                    )

                    # Add chunk label directly to page
                    add_text_to_page(
                        page,
                        fitz.Point(x0, y0 - 10),
                        f"Chunk {chunk_idx}",
                        color=chunk_color,
                        size=10,
                    )

    # Save and close the annotated PDF
    doc.save(output_path, incremental=True, encryption=0)
    doc.close()


def visualize_single_chunk(
    pdf_path: str,
    chunk,
    enriched_content_list: List,
    output_path: str = "chunk_visualization.pdf",
):
    """
    Create a PDF showing only the contents of a single chunk.
    """
    # Get content UUIDs for this chunk
    content_uuids = set(chunk.metadata["content_uuids"])

    # Filter content for this chunk
    chunk_content = [
        content for content in enriched_content_list if content.id in content_uuids
    ]

    # Create output directory if needed
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy the original PDF
    shutil.copy2(pdf_path, output_path)

    # Open the copied PDF and add annotations
    doc = fitz.open(output_path)

    # Get unique pages in this chunk
    chunk_pages = set(content.page_number for content in chunk_content)

    # Remove pages not in this chunk
    for page_num in reversed(range(len(doc))):
        if page_num not in chunk_pages:
            doc.delete_page(page_num)

    # Add annotations to remaining pages
    visualize_pdf_contents(
        doc,
        chunk_content,
        output_path=output_path,
        draw_chunks=False,  # No need for chunk boundaries in single chunk view
    )

    doc.close()
