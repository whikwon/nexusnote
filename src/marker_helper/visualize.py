from typing import Dict, List, Optional

import fitz  # PyMuPDF
from marker.renderers.json import JSONBlockOutput, JSONOutput
from pydantic import BaseModel

# Colors are RGB tuples with values between 0 and 1.
HIERARCHY_COLORS = {
    "document": (1, 0, 0),  # Red
    "section": (0, 1, 0),  # Green
    "subsection": (0, 0, 1),  # Blue
    "content": (0.8, 0.5, 0),  # Orange
    "table": (0.5, 0.5, 0.5),  # Gray for table-related blocks
}


def map_level_to_color(level: int) -> tuple:
    """
    Maps a numeric level to a color.
      - Level 1: document (red)
      - Level 2: section (green)
      - Level 3: subsection (blue)
      - Level 4+: content (orange)
    """
    if level == 1:
        return HIERARCHY_COLORS["document"]
    elif level == 2:
        return HIERARCHY_COLORS["section"]
    elif level == 3:
        return HIERARCHY_COLORS["subsection"]
    else:
        return HIERARCHY_COLORS["content"]


def traverse_marker_blocks(blocks: List[JSONBlockOutput]):
    """
    Recursively traverse the list of Marker blocks.
    Yields each block in the tree.
    """
    for block in blocks:
        yield block
        if block.children:
            yield from traverse_marker_blocks(block.children)


def get_page_number_from_block_id(block_id: str) -> int:
    """
    Extract the page number from a block's ID.
    Expected ID format (for example): "/page/0/SectionHeader/1"
    where the third token (index 2) is the page index.
    """
    parts = block_id.split("/")
    if len(parts) >= 3 and parts[1] == "page":
        try:
            return int(parts[2])
        except ValueError:
            pass
    return 0


def get_marker_block_level(block: JSONBlockOutput) -> int:
    """
    Determine a level for a Marker block based on its block_type.
      - "Page*"      -> Level 1 (document)
      - "Section*"   -> Level 2 (section)
      - "Table*"     -> Level 3 (table-related; treated similar to subsection)
      - Others       -> Level 4 (content)
    """
    bt = block.block_type.lower()
    if bt.startswith("page"):
        return 1
    elif bt.startswith("section"):
        return 2
    elif bt.startswith("table"):
        return 3
    else:
        return 4


# --- Main Visualization Function using Marker Data ---


def visualize_document_structure(
    pdf_path: str,
    marker: JSONOutput,
    output_pdf_path: str = "visualized_output.pdf",
):
    """
    Visualizes the document structure (from Marker data) on top of the original PDF.
    For each Marker block, this function draws:
      - A bounding box (using its bbox)
      - A text label containing its ID and block type
      - A dot at the center whose size indicates parent–child relationship:
          * Larger dot (radius=6) if the block has children (parent block)
          * Smaller dot (radius=3) if the block is a leaf (child block)

    Args:
        pdf_path (str): Path to the input PDF.
        marker (JSONOutput): Marker data structure containing the document blocks.
        output_pdf_path (str): Path to save the annotated PDF.
    """
    # Open the PDF using PyMuPDF.
    doc = fitz.open(pdf_path)

    # Build a mapping from block ID to block (if needed later).
    block_mapping: Dict[str, JSONBlockOutput] = {}
    for block in traverse_marker_blocks(marker.children):
        block_mapping[block.id] = block

    # --- Visualize each Marker block (bounding boxes, labels, and dots) ---
    for block in traverse_marker_blocks(marker.children):
        level = get_marker_block_level(block)
        node_color = map_level_to_color(level)

        page_number = get_page_number_from_block_id(block.id)
        if page_number < 0 or page_number >= len(doc):
            continue
        page = doc[page_number]

        # Ensure the bbox is valid (expects 4 numbers: [x0, y0, x1, y1])
        if not block.bbox or len(block.bbox) != 4:
            continue
        rect = fitz.Rect(block.bbox)

        # Draw the rectangle (stroke only) around the block.
        page.draw_rect(rect, color=node_color, width=1)

        # Insert a text label near the top-left corner of the bounding box.
        label_text = f"ID: {block.id}, Type: {block.block_type}"
        page.insert_text((rect.x0, rect.y0), label_text, color=node_color, fontsize=8)

        # Compute the center point of the rectangle.
        center = ((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)

        # Determine dot size: larger for parent blocks, smaller for child (leaf) blocks.
        if block.children and len(block.children) > 0:
            dot_radius = 6  # Larger dot for parent blocks.
        else:
            dot_radius = 3  # Smaller dot for leaf/child blocks.

        # Draw a filled circle (dot) at the center.
        page.draw_circle(center, radius=dot_radius, color=node_color, fill=node_color)

    # Save the annotated PDF and close the document.
    doc.save(output_pdf_path)
    doc.close()
    print(f"Visualization saved to {output_pdf_path}")
