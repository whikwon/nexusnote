from typing import Dict

import fitz  # PyMuPDF

# --- Define colors for hierarchy levels and relationship types ---
# Colors are RGB tuples with values between 0 and 1.
HIERARCHY_COLORS = {
    "document": (1, 0, 0),  # Red
    "section": (0, 1, 0),  # Green
    "subsection": (0, 0, 1),  # Blue
    "content": (0.8, 0.5, 0),  # Orange
}

RELATIONSHIP_COLORS = {
    "reference": (0.5, 0, 0.5),  # Purple
    "title": (0, 0.5, 0),  # Dark Green
    "citation": (0.5, 0.5, 0),  # Olive
    "footnote": (0, 0.5, 0.5),  # Teal
}


def map_level_to_color(level: int) -> tuple:
    """
    Maps a numeric level to a color.
      - Level 1: document
      - Level 2: section
      - Level 3: subsection
      - Level 4+: content
    """
    if level == 1:
        return HIERARCHY_COLORS["document"]
    elif level == 2:
        return HIERARCHY_COLORS["section"]
    elif level == 3:
        return HIERARCHY_COLORS["subsection"]
    else:
        return HIERARCHY_COLORS["content"]


def traverse_nodes(node_list):
    """
    Recursively traverse a list of GroupedNodes and yield each node.
    """
    for node in node_list:
        yield node
        if node.children:
            yield from traverse_nodes(node.children)


def visualize_document_structure(
    pdf_path: str,
    hierarchy,  # instance of DocumentHierarchy
    ref_manager,  # instance of ReferenceManager
    output_pdf_path: str = "visualized_output.pdf",
):
    """
    Visualizes the document structure (from the new hierarchy data structure) and relationships
    on top of the original PDF.

    Args:
        pdf_path (str): Path to the input PDF.
        hierarchy (DocumentHierarchy): The hierarchical structure built from TOC entries.
        ref_manager (ReferenceManager): Contains reference relationships between content boxes.
        output_pdf_path (str): Path to save the annotated PDF.
    """
    # Open the PDF using fitz.
    doc = fitz.open(pdf_path)

    # Build a mapping from each content box id to the box.
    box_mapping: Dict[str, any] = {}  # mapping: box_id -> PaddleXBoxContent
    # Traverse all nodes in the hierarchy.
    for node in traverse_nodes(hierarchy.root_nodes):
        for box in node.content_boxes:
            box_mapping[box.id] = box

    # --- 1. Visualize box contents (content boxes in each node) ---
    for node in traverse_nodes(hierarchy.root_nodes):
        # Determine a color based on node level.
        node_color = map_level_to_color(node.level)
        # Prepare a label for the node if available.
        node_label = f"ID: {node.id}"
        if node.title:
            node_label += f" ({node.title})"
        # Draw each content box in the node.
        for box in node.content_boxes:
            # Ensure the page exists (assuming page_number is 1-indexed)
            page_idx = box.page_number - 1
            if page_idx < 0 or page_idx >= len(doc):
                continue
            page = doc[page_idx]

            # Get the bounding box: assume box.bbox is [x0, y0, x1, y1]
            rect = fitz.Rect(box.bbox)

            # Draw a rectangle (using only a stroke, no fill) to highlight the content area.
            page.draw_rect(rect, color=node_color, width=1)

            # Insert a small text label near the top-left of the box.
            label_position = (rect.x0, rect.y0)
            page.insert_text(label_position, node_label, color=node_color, fontsize=8)

    # --- 2. Visualize relationships (references) ---
    for ref in ref_manager.relationships:
        # Determine the color for this relationship type.
        # If ref.rel_type is an enum, get its value; otherwise, use it directly.
        rel_type = (
            ref.rel_type.value if hasattr(ref.rel_type, "value") else ref.rel_type
        )
        dot_color = RELATIONSHIP_COLORS.get(
            rel_type.lower(), (0, 0, 0)
        )  # default black

        # For both source and target, add a colored dot at the center of the corresponding content box.
        for box_id in [ref.source_id, ref.target_id]:
            if box_id not in box_mapping:
                continue
            box = box_mapping[box_id]
            page_idx = box.page_number - 1
            page = doc[page_idx]
            rect = fitz.Rect(box.bbox)
            # Compute the center point of the rectangle.
            center = rect.tl + (rect.br - rect.tl) * 0.5
            # Draw a small filled circle (dot) at the center.
            if box_id == "86df912c-072f-491e-9182-fe59a025f60e":
                print(box)
            page.draw_circle(center, radius=3, color=dot_color, fill=dot_color)

    # Save the annotated PDF.
    doc.save(output_pdf_path)
    doc.close()
    print(f"Visualization saved to {output_pdf_path}")
