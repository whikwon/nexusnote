from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel

from .content_parser import PaddleXBoxContent
from .layout_parser import PaddleX17Cls


class RelationshipType(str, Enum):
    REFERENCE = "reference"
    TITLE = "title"
    CITATION = "citation"
    FOOTNOTE = "footnote"


class ReferenceRelationship(BaseModel):
    """
    Represents a relationship between two PaddleXBoxContent items.
    This might be used to create internal links within a PDF or track other references.
    """

    source_id: str  # id of the source content box
    target_id: str  # id of the target content box
    rel_type: str  # e.g. "internal_link", "citation", etc.
    distance: Optional[Tuple[float, int]] = None  # (spatial_distance, page_difference)
    ref_text: Optional[str] = None


class ReferenceManager:
    """
    Manages reference relationships between individual PaddleXBoxContent objects.
    This is maintained separately from the aggregated hierarchical structure.
    """

    def __init__(self):
        # Store relationships in a list.
        self.relationships: List[ReferenceRelationship] = []

    def add_reference(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        distance: Optional[Tuple[float, int]] = None,
        ref_text: Optional[str] = None,
    ) -> None:
        """
        Create and store a reference relationship between two content boxes.
        """
        relationship = ReferenceRelationship(
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            distance=distance,
            ref_text=ref_text,
        )
        self.relationships.append(relationship)

    def get_references_for_source(self, source_id: str) -> List[ReferenceRelationship]:
        """
        Retrieve all relationships where the given content box is the source.
        """
        return [r for r in self.relationships if r.source_id == source_id]

    def get_all_references(self) -> List[ReferenceRelationship]:
        """
        Retrieve the full list of reference relationships.
        """
        return self.relationships

    def find_reference_by_target(self, target_id: str) -> List[ReferenceRelationship]:
        """
        Retrieve all relationships that target the specified content box.
        """
        return [r for r in self.relationships if r.target_id == target_id]

    @staticmethod
    def compute_box_distance(
        box1: PaddleXBoxContent, box2: PaddleXBoxContent, page_height: float = 1000
    ) -> Tuple[float, int]:
        """
        Computes a distance metric between two boxes.
        If the boxes are on the same page, the distance is the absolute difference
        between their vertical centers.

        If the boxes are on different pages, the spatial distance is computed as:
          - the distance from the center of box1 to the bottom of its page,
          - plus the distance from the top of box2's page to the center of box2,
          - plus the full page heights for any intermediate pages.

        Args:
            box1 (PaddleXBoxContent): The first content box.
            box2 (PaddleXBoxContent): The second content box.
            page_height (float): The assumed height of a page.

        Returns:
            Tuple[float, int]: A tuple containing the computed spatial distance and the page difference.
        """
        page_diff = abs(box1.page_number - box2.page_number)
        center1_y = (box1.bbox[1] + box1.bbox[3]) / 2
        center2_y = (box2.bbox[1] + box2.bbox[3]) / 2

        if page_diff == 0:
            spatial_distance = abs(center2_y - center1_y)
        else:
            # Calculate the distance from box1's center to the bottom of its page.
            distance_box1 = page_height - center1_y
            # Calculate the distance from the top of box2's page to its center.
            distance_box2 = center2_y
            # Include full page heights for any pages in between box1 and box2.
            spatial_distance = (
                distance_box1 + distance_box2 + page_height * (page_diff - 1)
            )

        return spatial_distance, page_diff

    def add_internal_link(
        self,
        source_box: PaddleXBoxContent,
        target_box: PaddleXBoxContent,
        rel_type: str = "internal_link",
        ref_text: Optional[str] = None,
        page_height: float = 1000,
    ) -> None:
        """
        Convenience method for adding an internal link between two content boxes.
        It computes the distance metric automatically using the given page height.
        """
        distance = self.compute_box_distance(source_box, target_box, page_height)
        self.add_reference(source_box.id, target_box.id, rel_type, distance, ref_text)


def add_title_content_references(
    content_list: List[PaddleXBoxContent],
    ref_manager: ReferenceManager,
    page_height: float,
    max_page_diff: int = 1,
) -> None:
    """
    Creates title-content reference relationships. For each title-like box (e.g. chart_title,
    table_title), this function finds the nearest box of the corresponding target type (e.g.
    picture or table) that is on the same or a neighboring page and adds a reference between them.

    Args:
        content_list (List[PaddleXBoxContent]): All content boxes in the document.
        ref_manager (ReferenceManager): The reference manager used to store relationships.
        page_height (float): The height of a page in the current PDF file.
        max_page_diff (int): Maximum allowed page difference when matching title to content.
    """
    # Define mapping: title box type -> (target content type, relationship type)
    content_relationships = {
        PaddleX17Cls.chart_title: (PaddleX17Cls.picture, RelationshipType.TITLE),
        PaddleX17Cls.table_title: (PaddleX17Cls.table, RelationshipType.TITLE),
    }

    # For each box in the content list, if it's a title type, search for the nearest content box.
    for title_box in content_list:
        if title_box.cls_id in content_relationships:
            target_type, rel_type = content_relationships[title_box.cls_id]
            candidate_box = None
            min_distance = float("inf")

            # Look for candidate boxes that match the target type.
            for candidate in content_list:
                if candidate.cls_id == target_type:
                    # Check that the candidate is on the same page or within max_page_diff pages.
                    if (
                        abs(candidate.page_number - title_box.page_number)
                        <= max_page_diff
                    ):
                        distance, _ = ReferenceManager.compute_box_distance(
                            title_box, candidate, page_height
                        )
                        if distance < min_distance:
                            min_distance = distance
                            candidate_box = candidate

            # If a candidate is found, add a title-content relationship.
            if candidate_box is not None:
                ref_manager.add_internal_link(
                    title_box, candidate_box, rel_type=rel_type, page_height=page_height
                )
