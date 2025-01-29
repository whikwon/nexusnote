import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from src.pdf_helper.content_extractor import (
    EnrichedPaddleXBoxContent,
    PaddleX17Cls,
    PaddleXBoxContent,
    Reference,
    ReferenceType,
)


class ContentRelationship(BaseModel):
    source_id: str
    target_id: str
    ref_type: ReferenceType
    ref_text: str


class ContentLinker:
    # Class-level pattern definitions
    REFERENCE_PATTERN_TEMPLATES: Dict[ReferenceType, str] = {
        ReferenceType.TABLE: r"Table\s+(\d+(?:\.\d+)?)",
        ReferenceType.FIGURE: r"(?:Figure|Fig\.)\s+(\d+(?:\.\d+)?)",
        ReferenceType.EQUATION: r"(?:Equation|Eq\.)\s+(\d+(?:\.\d+)?)",
        ReferenceType.SECTION: r"Section\s+(\d+(?:\.\d+)?)",
        ReferenceType.ALGORITHM: r"Algorithm\s+(\d+(?:\.\d+)?)",
    }

    # Class-level mapping of PaddleX17Cls to ReferenceType
    CLS_TO_REF_TYPE: Dict[PaddleX17Cls, ReferenceType] = {
        PaddleX17Cls.table_title: ReferenceType.TABLE,
        PaddleX17Cls.chart_title: ReferenceType.FIGURE,
        # Add more mappings as needed
    }

    def __init__(self):
        # Compile patterns during initialization
        self.reference_patterns: Dict[ReferenceType, re.Pattern] = {
            ref_type: re.compile(pattern, re.IGNORECASE)
            for ref_type, pattern in self.REFERENCE_PATTERN_TEMPLATES.items()
        }

    def _extract_number_from_title(
        self, text: str, ref_type: ReferenceType
    ) -> Optional[str]:
        """Extract the reference number from a title."""
        pattern = self.reference_patterns[ref_type]
        match = pattern.search(text)
        return match.group(1) if match else None

    def _find_references_in_text(self, text: str) -> List[Tuple[ReferenceType, str]]:
        """Find all references in a text and return list of (type, number) tuples."""
        references = []
        for ref_type, pattern in self.reference_patterns.items():
            for match in pattern.finditer(text):
                references.append((ref_type, match.group(1)))
        return references

    def create_relationships(
        self, content_list: List[EnrichedPaddleXBoxContent]
    ) -> List[ContentRelationship]:
        """Create relationships between content items based on references."""
        title_index: Dict[ReferenceType, Dict[str, str]] = defaultdict(dict)
        relationships: List[ContentRelationship] = []

        # First pass: Create index of titles
        for content in content_list:
            cls_id = content.cls_id
            if cls_id in self.CLS_TO_REF_TYPE:
                ref_type = self.CLS_TO_REF_TYPE[cls_id]
                if content.text:  # Check if text exists
                    number = self._extract_number_from_title(content.text, ref_type)
                    if number is not None:
                        title_index[ref_type][number] = content.id

        # Second pass: Find references in text
        for content in content_list:
            if not content.text:
                continue

            references = self._find_references_in_text(content.text)
            for ref_type, ref_number in references:
                if ref_number in title_index[ref_type]:
                    target_id = title_index[ref_type][ref_number]
                    if target_id != content.id:  # Avoid self-references
                        relationships.append(
                            ContentRelationship(
                                source_id=content.id,
                                target_id=target_id,
                                ref_type=ref_type,
                                ref_text=f"{ref_type.title()} {ref_number}",
                            )
                        )

        return relationships

    def enrich_content(
        self,
        content_list: List[EnrichedPaddleXBoxContent],  # Change type hint
        relationships: List[ContentRelationship],
    ) -> List[EnrichedPaddleXBoxContent]:
        """Enrich content items with relationship information."""
        # Create id mapping from existing enriched content
        id_to_content: Dict[str, EnrichedPaddleXBoxContent] = {
            content.id: content for content in content_list
        }

        # Add relationship information
        for rel in relationships:
            source = id_to_content[rel.source_id]
            target = id_to_content[rel.target_id]

            source.references_to.append(
                Reference(
                    target_id=rel.target_id,
                    type=rel.ref_type,
                    text=rel.ref_text,
                )
            )

            target.referenced_by.append(
                Reference(
                    target_id=rel.source_id,
                    type=rel.ref_type,
                    text=rel.ref_text,
                )
            )

        return content_list


def process_document_relationships(
    content_list: List[PaddleXBoxContent],
) -> List[EnrichedPaddleXBoxContent]:
    """Process and enrich content with relationships."""
    linker = ContentLinker()

    # Create enriched content once and reuse it
    enriched_content = [
        EnrichedPaddleXBoxContent(
            page_number=content.page_number,
            bbox=content.bbox,
            cls_id=content.cls_id,
            text=content.text,
            image=content.image,
            references_to=[],
            referenced_by=[],
        )
        for content in content_list
    ]

    # Use the same enriched content objects for both operations
    relationships = linker.create_relationships(enriched_content)
    final_enriched_content = linker.enrich_content(enriched_content, relationships)
    return final_enriched_content
