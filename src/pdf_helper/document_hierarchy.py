from typing import List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field
from rapidfuzz import fuzz

# (Assuming these are imported from your existing modules)
from .content_parser import PaddleXBoxContent
from .toc_extractor import TocEntry


class HierarchyNode(BaseModel):
    id: str
    level: int
    content: PaddleXBoxContent
    parent_id: Optional[str] = None
    children: List[str] = []


class GroupedNode(BaseModel):
    """
    Represents an aggregated node in the document hierarchy.
    Each node is assigned a new unique id, a numeric level, an optional title,
    and may contain a list of grouped content boxes as well as child nodes.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    level: int  # e.g. 1 for top-level sections, 2 for subsections, etc.
    title: Optional[str] = None  # A representative title if available.
    page_number: Optional[int] = None  # TOC page number for grouping reference.
    content_boxes: List[PaddleXBoxContent] = []  # All boxes grouped in this node.
    children: List["GroupedNode"] = []  # Child nodes within this group.
    parent_id: Optional[str] = None  # Optional parent node id.

    class Config:
        orm_mode = True


# Resolve forward references.
GroupedNode.update_forward_refs()


class DocumentHierarchy(BaseModel):
    """
    Represents the overall document hierarchy.
    It stores a list of top-level nodes. Each node aggregates a group of related content boxes.
    """

    root_nodes: List[GroupedNode] = []

    def add_node(self, node: GroupedNode) -> None:
        """Add a new top-level node to the document hierarchy."""
        self.root_nodes.append(node)

    def traverse(self) -> List[GroupedNode]:
        """Traverse the hierarchy and return all nodes (e.g., for debugging or analysis)."""
        all_nodes = []

        def _collect(node: GroupedNode):
            all_nodes.append(node)
            for child in node.children:
                _collect(child)

        for root in self.root_nodes:
            _collect(root)
        return all_nodes

    def find_by_id(self, node_id: str) -> Optional[GroupedNode]:
        """Search for a node by its unique id."""
        for node in self.traverse():
            if node.id == node_id:
                return node
        return None


def build_document_hierarchy(
    content_list: List[PaddleXBoxContent],
    toc_entries: List[TocEntry],  # TOC entries from dynamic_extract_hierarchy
    title_similarity_threshold: int = 80,  # fuzzy matching threshold (0-100)
) -> Tuple[DocumentHierarchy]:
    """
    Builds a grouped document hierarchy based on TOC entries and manages reference relationships.

    Revised approach details:
      1. Create a list of GroupedNodes (one per TOC entry).
      2. Sort these nodes and the content boxes in reading order.
      3. Stream through the content boxes. When a header-like box is encountered (its text fuzzily
         matches a TOC entry), update the "current_section" pointer.
         - If the header is the same as the current section’s title and we've already collected some boxes,
           then we assume that this is a new occurrence of that section header. In that case, we create a new
           GroupedNode for this occurrence.
         - Otherwise, we update the current_section pointer to the matching header node.
      4. All subsequent boxes (until the next header occurrence) are added to the current section.
      5. Finally, we build parent-child relationships among the nodes.
    """
    # --- 1. Create initial GroupedNodes from TOC entries ---
    # (These serve as “prototypes” for matching; later new occurrences may be added if a header repeats.)
    toc_nodes: List[GroupedNode] = []
    for toc in toc_entries:
        node = GroupedNode(
            level=toc.level,
            title=toc.title,
            page_number=toc.page_number,
            content_boxes=[],  # initially empty; we will add boxes sequentially
        )
        toc_nodes.append(node)

    # --- 2. Sort content boxes in reading order: by page number then by top coordinate ---
    content_boxes_sorted = sorted(
        content_list, key=lambda b: (b.page_number, b.bbox[1])
    )

    # We now use a "current_section" pointer to remember the most recent header (GroupedNode)
    current_section: Optional[GroupedNode] = None

    # --- 3. Process each content box sequentially ---
    for box in content_boxes_sorted:
        header_detected = False
        if box.text is not None and box.text.content:
            # Check among toc_nodes that have "appeared" (by page) whether this box looks like a header.
            potential_matches = [
                node
                for node in toc_nodes
                if node.page_number == box.page_number
                and fuzz.token_set_ratio(box.text.content, node.title)
                >= title_similarity_threshold
            ]
            if potential_matches:
                # Use the most recent (last) matching TOC node.
                matched = potential_matches[-1]
                # If we already have a current section with the same title and it already contains some boxes,
                # then assume that this header reoccurs and a new section should start.
                if (
                    current_section is not None
                    and current_section.title == matched.title
                    and current_section.content_boxes
                ):
                    # Create a new node for this new occurrence.
                    new_section = GroupedNode(
                        level=matched.level,
                        title=matched.title,
                        page_number=box.page_number,
                        content_boxes=[box],  # add the header box immediately
                    )
                    # Optionally, register this new section in our toc_nodes list.
                    toc_nodes.append(new_section)
                    current_section = new_section
                else:
                    # Otherwise, update the current_section to the matched node.
                    current_section = matched
                    # Add the header box if it isn't already in the list.
                    if box not in current_section.content_boxes:
                        current_section.content_boxes.append(box)
                header_detected = True
                # Skip adding the box again below.
                continue

        # --- 4. For non-header boxes (or boxes that did not trigger a header change) ---
        if not header_detected and current_section is not None:
            current_section.content_boxes.append(box)
        # (Boxes for which no header has been detected yet remain unassigned.
        #  You may choose to handle them as needed.)

    # --- 5. Build parent-child relationships among the TOC nodes based on level and order ---
    # Here, we iterate over all nodes (including those added for repeated headers).
    # For each node, we search backwards for a node with a lower level.
    for i, node in enumerate(toc_nodes):
        for potential_parent in reversed(toc_nodes[:i]):
            if (
                potential_parent.page_number <= node.page_number
                and potential_parent.level < node.level
            ):
                node.parent_id = potential_parent.id
                potential_parent.children.append(node)
                break

    # Build the final DocumentHierarchy: add only top-level nodes (nodes without a parent).
    hierarchy = DocumentHierarchy()
    for node in toc_nodes:
        if node.parent_id is None:
            hierarchy.add_node(node)

    return hierarchy
