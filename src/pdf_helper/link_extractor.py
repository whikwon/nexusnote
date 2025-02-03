import re
from collections import defaultdict
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel

from src.pdf_helper.content_extractor import (
    PaddleX17Cls,
    PaddleXBoxContent,
    ReferenceType,
)


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


class ContentRelationship(BaseModel):
    source_id: str
    target_id: str
    ref_type: ReferenceType
    ref_text: str


class ContentLinker:
    REFERENCE_PATTERN_TEMPLATES: Dict[ReferenceType, str] = {
        ReferenceType.TABLE: r"Table\s+(\d+(?:\.\d+)?)",
        ReferenceType.FIGURE: r"(?:Figure|Fig\.)\s+(\d+(?:\.\d+)?)",
        ReferenceType.EQUATION: r"(?:Equation|Eq\.)\s+(\d+(?:\.\d+)?)",
        ReferenceType.SECTION: r"Section\s+(\d+(?:\.\d+)?)",
        ReferenceType.ALGORITHM: r"Algorithm\s+(\d+(?:\.\d+)?)",
    }
    CLS_TO_REF_TYPE: Dict[PaddleX17Cls, ReferenceType] = {
        PaddleX17Cls.table_title: ReferenceType.TABLE,
        PaddleX17Cls.chart_title: ReferenceType.FIGURE,
        # Add more mappings as needed.
    }

    def __init__(self):
        self.reference_patterns: Dict[ReferenceType, re.Pattern] = {
            ref_type: re.compile(pattern, re.IGNORECASE)
            for ref_type, pattern in self.REFERENCE_PATTERN_TEMPLATES.items()
        }

    def _extract_number_from_title(
        self, text: str, ref_type: ReferenceType
    ) -> Optional[str]:
        pattern = self.reference_patterns[ref_type]
        match = pattern.search(text)
        return match.group(1) if match else None

    def _find_references_in_text(self, text: str) -> List[Tuple[ReferenceType, str]]:
        references = []
        for ref_type, pattern in self.reference_patterns.items():
            for match in pattern.finditer(text):
                references.append((ref_type, match.group(1)))
        return references

    def create_relationships(
        self, content_list: List[PaddleXBoxContent]
    ) -> List[ContentRelationship]:
        title_index: Dict[ReferenceType, Dict[str, str]] = defaultdict(dict)
        relationships: List[ContentRelationship] = []
        # Build an index of titles from content that have reference numbers.
        for content in content_list:
            cls_id = content.cls_id
            if cls_id in self.CLS_TO_REF_TYPE and content.text:
                ref_type = self.CLS_TO_REF_TYPE[cls_id]
                number = self._extract_number_from_title(content.text.content, ref_type)
                if number is not None:
                    title_index[ref_type][number] = content.id
        # Find references in the text of each content.
        for content in content_list:
            if not content.text:
                continue
            refs = self._find_references_in_text(content.text.content)
            for ref_type, ref_number in refs:
                if ref_number in title_index[ref_type]:
                    target_id = title_index[ref_type][ref_number]
                    if target_id != content.id:
                        relationships.append(
                            ContentRelationship(
                                source_id=content.id,
                                target_id=target_id,
                                ref_type=ref_type,
                                ref_text=f"{ref_type.title()} {ref_number}",
                            )
                        )
        return relationships
