
import fitz  # PyMuPDF
from marker.renderers.json import JSONBlockOutput, JSONOutput

# Colors for hierarchy levels. Keys represent the hierarchy level.
HIERARCHY_COLOR_MAP = {
    1: (1, 0, 0),  # Red for top-level (e.g. Document)
    2: (0, 1, 0),  # Green for level-2 sections
    3: (0, 0, 1),  # Blue for level-3 sections
    4: (0.8, 0.5, 0),  # Orange for level-4 (or deeper)
}

# Colors for individual items based on block type.
ITEM_COLOR_MAP = {
    "TableGroup": (0.5, 0.5, 0.5),  # Gray for TableGroup
    "FigureGroup": (1, 0.5, 0),  # Orange-Red for FigureGroup
    # Other specific item types can be added here.
}

# Default item color if block type is not explicitly mapped.
DEFAULT_ITEM_COLOR = (0, 0, 0)  # Black


# Fallback hierarchy color (if no section_hierarchy is present).
def default_hierarchy_color(block) -> tuple:
    # Use the heuristic level from the block type.
    level = get_marker_block_level(block)
    return map_level_to_color(level)


def map_level_to_color(level: int) -> tuple:
    """
    Returns a color based on a numeric level using our HIERARCHY_COLOR_MAP.
    If the level is not explicitly defined, returns a default color.
    """
    return HIERARCHY_COLOR_MAP.get(level, (0.8, 0.5, 0))


def traverse_marker_blocks(blocks: list[JSONBlockOutput]):
    """
    Recursively traverse the list of Marker blocks and yield each block.
    """
    for block in blocks:
        yield block
        if block.children:
            yield from traverse_marker_blocks(block.children)


def get_page_number_from_block_id(block_id: str) -> int:
    """
    Extract the page number from a block's ID.
    Expected format: "/page/0/SectionHeader/1" where the third token (index 2)
    is the page index.
    """
    parts = block_id.split("/")
    if len(parts) >= 3 and parts[1] == "page":
        try:
            return int(parts[2])
        except ValueError:
            pass
    return 0


def polygon_to_rect(poly: list[list[float]]) -> fitz.Rect:
    """
    Convert a polygon (list of four [x, y] points) to a bounding rectangle.
    Computes min/max coordinates and returns a fitz.Rect.
    """
    xs = [pt[0] for pt in poly]
    ys = [pt[1] for pt in poly]
    return fitz.Rect(min(xs), min(ys), max(xs), max(ys))


def get_marker_block_level(block: JSONBlockOutput) -> int:
    """
    Determine a hierarchical level for a Marker block based on its block_type.

    Heuristic (if section_hierarchy is not used):
      - "Document" or "Page"           -> Level 1
      - "SectionHeader", "PageHeader", "PageFooter", "TableOfContents"
                                        -> Level 2
      - "TableGroup", "FigureGroup", "ListGroup", "PictureGroup"
                                        -> Level 3
      - All other types                -> Level 4
    """
    bt = block.block_type
    if bt in ["Document", "Page"]:
        return 1
    elif bt in ["SectionHeader", "PageHeader", "PageFooter", "TableOfContents"]:
        return 2
    elif bt in ["TableGroup", "FigureGroup", "ListGroup", "PictureGroup"]:
        return 3
    else:
        return 4


def get_hierarchy_color(block: JSONBlockOutput) -> tuple:
    """
    Determines the hierarchy color based on the block's section_hierarchy.
    If section_hierarchy exists, we use the deepest level (maximum key)
    to select a color from HIERARCHY_COLOR_MAP. Otherwise, fallback to the default
    heuristic based on the block type.
    """
    if block.section_hierarchy and len(block.section_hierarchy) > 0:
        # Use the deepest hierarchy level (assumed to be the maximum key).
        hierarchy_level = max(block.section_hierarchy.keys())
        return HIERARCHY_COLOR_MAP.get(hierarchy_level, default_hierarchy_color(block))
    else:
        return default_hierarchy_color(block)


def get_item_color(block: JSONBlockOutput) -> tuple:
    """
    Determines the item color based solely on the block's type.
    If the block_type is present in ITEM_COLOR_MAP, use that color;
    otherwise, return a default item color.
    """
    return ITEM_COLOR_MAP.get(block.block_type, DEFAULT_ITEM_COLOR)


def visualize_document_structure(
    pdf_path: str, marker: JSONOutput, output_pdf_path: str = "visualized_output.pdf"
):
    """
    Visualizes the document structure from Marker data on top of the original PDF.

    For each Marker block (except those with block_type "Table"), this function:
      - Computes a bounding rectangle from its polygon.
      - Draws the rectangle and a text label (ID and block_type) using the hierarchy color.
      - Draws a dot at the center using the item color. The dot is larger (radius=6) if the block
        has children, or smaller (radius=3) if it is a leaf.

    Args:
      pdf_path: Path to the input PDF.
      marker: Marker JSON output containing document blocks.
      output_pdf_path: Path to save the annotated PDF.
    """
    doc = fitz.open(pdf_path)

    # (Optional) Build a mapping from block id to block.
    block_mapping: dict[str, JSONBlockOutput] = {}
    for block in traverse_marker_blocks(marker.children):
        block_mapping[block.id] = block

    # Visualize each Marker block.
    for block in traverse_marker_blocks(marker.children):
        # Omit blocks that are individual table cells.
        if block.block_type == "TableCell":
            continue

        # Determine the two colors:
        hierarchy_color = get_hierarchy_color(block)
        item_color = get_item_color(block)

        page_num = get_page_number_from_block_id(block.id)
        if page_num < 0 or page_num >= len(doc):
            continue
        page = doc[page_num]

        # Validate the polygon (expects exactly 4 points).
        if not block.polygon or len(block.polygon) != 4:
            continue

        # Compute a bounding rectangle from the polygon.
        rect = polygon_to_rect(block.polygon)

        # Draw the rectangle using the hierarchy color.
        page.draw_rect(rect, color=hierarchy_color, width=1)

        # Insert a text label (using the hierarchy color) at the top-left of the rectangle.
        label = f"ID: {block.id}\nType: {block.block_type}"
        page.insert_text((rect.x0, rect.y0), label, color=hierarchy_color, fontsize=8)

        # Compute the center of the rectangle.
        center = ((rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2)

        # Determine dot size: larger if the block has children, smaller if it is a leaf.
        radius = 6 if block.children and len(block.children) > 0 else 3

        # Draw the dot using the item color.
        page.draw_circle(center, radius=radius, color=item_color, fill=item_color)

    # Save the annotated PDF and close the document.
    doc.save(output_pdf_path)
    doc.close()
    print(f"Visualization saved to {output_pdf_path}")
