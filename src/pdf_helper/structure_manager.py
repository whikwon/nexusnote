from enum import Enum
from typing import Dict, List, Optional, Tuple

from langchain_core.documents import Document as LangChainDocument
from pydantic import BaseModel

from .content_parser import PaddleXBoxContent
from .layout_parser import PaddleX17Cls


class HierarchyLevel(str, Enum):
    DOCUMENT = "document"
    SECTION = "section"
    SUBSECTION = "subsection"
    CONTENT = "content"


class HierarchyNode(BaseModel):
    id: str
    level: HierarchyLevel
    content: PaddleXBoxContent
    parent_id: Optional[str] = None
    children: List[str] = []


class RelationshipType(str, Enum):
    REFERENCE = "reference"
    TITLE = "title"
    CITATION = "citation"
    FOOTNOTE = "footnote"


class ReferenceRelationship(BaseModel):
    source_id: str
    target_id: str
    rel_type: RelationshipType
    distance: Optional[Tuple[float, int]] = None  # (spatial_distance, page_difference)
    ref_text: Optional[str] = None


class StaticDocumentStructure:
    def __init__(self):
        self.nodes: Dict[str, HierarchyNode] = {}
        self.root_ids: List[str] = []
        self.references: List[ReferenceRelationship] = []

    def _get_hierarchy_level(self, content: PaddleXBoxContent) -> HierarchyLevel:
        """Determines the hierarchy level for a content box."""
        if content.cls_id != PaddleX17Cls.paragraph_title or content.text is None:
            return HierarchyLevel.CONTENT
        fonts = content.text.fonts
        max_font_size = max(font.size for font in fonts)
        if max_font_size > 16:
            return HierarchyLevel.SECTION
        elif max_font_size > 14:
            return HierarchyLevel.SUBSECTION
        else:
            return HierarchyLevel.CONTENT

    def add_node(self, content: PaddleXBoxContent, level: HierarchyLevel) -> str:
        """Creates and stores a HierarchyNode from the given content."""
        node = HierarchyNode(
            id=content.id, level=level, content=content, parent_id=None, children=[]
        )
        self.nodes[content.id] = node
        return content.id

    def get_ordered_nodes(self) -> List[HierarchyNode]:
        """
        Returns a list of all hierarchy nodes sorted by page number and the y-coordinate (top)
        of their bounding box. This ordering reflects the natural reading order of the document.
        """
        return sorted(
            self.nodes.values(),
            key=lambda node: (node.content.page_number, node.content.bbox[1]),
        )

    def build_hierarchy(self, boxes: List[PaddleXBoxContent]) -> None:
        """Builds a tree hierarchy from content boxes."""
        sorted_boxes = sorted(boxes, key=lambda x: (x.page_number, x.bbox[1]))
        current_section: Optional[str] = None
        current_subsection: Optional[str] = None

        for box in sorted_boxes:
            level = self._get_hierarchy_level(box)
            node_id = self.add_node(box, level)

            if level == HierarchyLevel.SECTION:
                self.nodes[node_id].parent_id = None
                self.root_ids.append(node_id)
                current_section = node_id
                current_subsection = None
            elif level == HierarchyLevel.SUBSECTION:
                if current_section:
                    self.nodes[node_id].parent_id = current_section
                    self.nodes[current_section].children.append(node_id)
                else:
                    self.nodes[node_id].parent_id = None
                    self.root_ids.append(node_id)
                current_subsection = node_id
            else:  # CONTENT level
                parent = current_subsection if current_subsection else current_section
                if parent:
                    self.nodes[node_id].parent_id = parent
                    self.nodes[parent].children.append(node_id)
                else:
                    self.nodes[node_id].parent_id = None
                    self.root_ids.append(node_id)

    def _calculate_box_distance(
        self, box1: PaddleXBoxContent, box2: PaddleXBoxContent
    ) -> Tuple[float, int]:
        """Computes spatial distance between boxes."""
        page_diff = abs(box1.page_number - box2.page_number)
        center1_y = (box1.bbox[1] + box1.bbox[3]) / 2
        center2_y = (box2.bbox[1] + box2.bbox[3]) / 2
        spatial_distance = abs(center2_y - center1_y)
        return spatial_distance, page_diff

    def _find_nearest_content(
        self,
        target_box: PaddleXBoxContent,
        content_type: PaddleX17Cls,
        max_boxes: int = 5,
        max_pages: int = 1,
    ) -> Optional[str]:
        """Finds the nearest content box of a given type."""
        candidates = [
            node for node in self.nodes.values() if node.content.cls_id == content_type
        ]
        if not candidates:
            return None

        sorted_candidates = sorted(
            candidates,
            key=lambda node: (node.content.page_number, node.content.bbox[1]),
        )
        target_page = target_box.page_number
        target_y = target_box.bbox[1]

        insertion_point = len(sorted_candidates)
        for i, candidate in enumerate(sorted_candidates):
            if candidate.content.page_number > target_page or (
                candidate.content.page_number == target_page
                and candidate.content.bbox[1] > target_y
            ):
                insertion_point = i
                break

        start_idx = max(0, insertion_point - max_boxes)
        end_idx = min(len(sorted_candidates), insertion_point + max_boxes)

        min_distance = float("inf")
        min_page_diff = float("inf")
        nearest_id = None

        for i in range(start_idx, end_idx):
            candidate = sorted_candidates[i]
            page_diff = abs(candidate.content.page_number - target_page)
            if page_diff > max_pages:
                continue
            spatial_distance, curr_page_diff = self._calculate_box_distance(
                target_box, candidate.content
            )
            if curr_page_diff < min_page_diff or (
                curr_page_diff == min_page_diff and spatial_distance < min_distance
            ):
                min_distance = spatial_distance
                min_page_diff = curr_page_diff
                nearest_id = candidate.id
        return nearest_id

    def add_reference_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        distance: Optional[Tuple[float, int]] = None,
        ref_text: Optional[str] = None,
    ) -> None:
        """Creates and stores a reference relationship between two nodes."""
        reference = ReferenceRelationship(
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            distance=distance,
            ref_text=ref_text,
        )
        self.references.append(reference)

    def add_title_references(self) -> None:
        """Creates references between titles and their corresponding content."""
        content_relationships = {
            PaddleX17Cls.chart_title: (PaddleX17Cls.picture, RelationshipType.TITLE),
            PaddleX17Cls.table_title: (PaddleX17Cls.table, RelationshipType.TITLE),
        }

        for node in self.nodes.values():
            if node.content.cls_id in content_relationships:
                target_type, rel_type = content_relationships[node.content.cls_id]
                nearest_id = self._find_nearest_content(node.content, target_type)
                if nearest_id:
                    candidate = self.nodes[nearest_id]
                    distance = self._calculate_box_distance(
                        node.content, candidate.content
                    )
                    self.add_reference_relationship(
                        source_id=node.id,
                        target_id=candidate.id,
                        rel_type=rel_type,
                        distance=distance,
                    )

    def build_references(self) -> None:
        """Builds all reference relationships in the document."""
        self.add_title_references()
        # Add other reference building methods here if needed.
