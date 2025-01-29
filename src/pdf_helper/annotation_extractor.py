import re
from typing import Dict, List, Optional, Set, Tuple

import fitz


class PDFAnnotationExtractor:
    def __init__(self, pdf_path: str):
        """Initialize the extractor with a PDF file path."""
        self.doc = fitz.open(pdf_path)
        self.existing_links = self._get_existing_links()

        # Compile patterns once during initialization
        self.patterns = {
            "figure": re.compile(
                r"(Figure|Fig\.?)\s+(\d+[A-Za-z]?(?:[-–]\d+[A-Za-z]?)?)", re.IGNORECASE
            ),
            "table": re.compile(
                r"(Table)\s+(\d+[A-Za-z]?(?:[-–]\d+[A-Za-z]?)?)", re.IGNORECASE
            ),
            "equation": [
                # Standard equation references
                re.compile(r"(Equation|Eq\.?)\s+(\d+(?:\.\d+)*)", re.IGNORECASE),
                # Parenthetical equation numbers like (1) or (1.2)
                re.compile(r"\((\d+(?:\.\d+)*)\)(?!\s*[a-zA-Z])"),
                # Eqs. (1)-(3) format
                re.compile(
                    r"(Equations|Eqs\.?)\s+\((\d+)(?:[-–](\d+))?\)", re.IGNORECASE
                ),
                # References like (1.1a)
                re.compile(r"\((\d+(?:\.\d+)*[a-z]?)\)"),
            ],
            "section": [
                # Standard section references
                re.compile(r"(Section|Sect\.?)\s+(\d+(?:\.\d+)*)", re.IGNORECASE),
                # Chapter/Section number only format (e.g., "3.2")
                re.compile(r"(?<!\d)(\d+\.\d+(?:\.\d+)*)(?!\d)"),
                # Chapter-Section format
                re.compile(
                    r"(Chapter|Chap\.?)\s+(\d+)(?:[,\s]+[Ss]ection\s+(\d+(?:\.\d+)*))?",
                    re.IGNORECASE,
                ),
                # Parenthetical section references
                re.compile(r"\((?:Section|Sect\.?)\s+(\d+(?:\.\d+)*)\)", re.IGNORECASE),
                # § symbol with numbers
                re.compile(r"(?:§|§§)\s*(\d+(?:\.\d+)*)"),
            ],
        }

    def _get_existing_links(self) -> Set[Tuple[int, float, float, float, float]]:
        """
        Get existing internal links in the PDF to avoid duplicates.
        Returns a set of tuples (page_num, x0, y0, x1, y1) representing link areas.
        """
        existing_links = set()
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            for link in page.get_links():
                kind = link["kind"]
                if kind in [
                    fitz.LINK_GOTO,
                    fitz.LINK_URI,
                    fitz.LINK_NAMED,
                    fitz.LINK_GOTOR,
                ]:
                    rect = link["from"]
                    existing_links.add((page_num, rect.x0, rect.y0, rect.x1, rect.y1))
        return existing_links

    def _is_overlapping_with_existing(self, page_num: int, rect: fitz.Rect) -> bool:
        """Check if a rectangle overlaps with any existing internal links."""
        return any(
            page_num == existing_page
            and not (rect.x1 < ex0 or rect.x0 > ex1 or rect.y1 < ey0 or rect.y0 > ey1)
            for existing_page, ex0, ey0, ex1, ey1 in self.existing_links
        )

    def find_equation_numbers(self) -> List[Dict]:
        """
        Find standalone equation numbers that appear at the right margin.
        These are typically the actual equations in the document, not references to them.
        """
        equation_numbers = []

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            blocks = page.get_text("blocks")
            page_width = page.rect.width

            for block in blocks:
                x0, y0, x1, y1, text, block_no, block_type = block

                # Check if block is near right margin (last 20% of page width)
                if x0 > page_width * 0.8:
                    # Look for standalone equation numbers
                    match = re.match(r"^\s*\((\d+(?:\.\d+)*[a-z]?)\)\s*$", text.strip())
                    if match:
                        equation_numbers.append(
                            {
                                "type": "equation_number",
                                "text": match.group(0),
                                "number": match.group(1),
                                "page": page_num,
                                "rect": fitz.Rect(x0, y0, x1, y1),
                            }
                        )

        return equation_numbers

    def _check_reference_match(
        self, words: List[Tuple], i: int
    ) -> Tuple[Optional[str], Optional[str], Optional[fitz.Rect], int]:
        """
        Check if the current word(s) match any reference pattern.
        Returns (ref_type, ref_text, rect, next_index).
        """
        if i >= len(words):
            return None, None, None, i + 1

        word = words[i][4]

        # Check for figure and table references
        for ref_type in ["figure", "table"]:
            pattern = self.patterns[ref_type]
            # Check current word or current + next word
            match = pattern.match(word)
            if not match and i + 1 < len(words):
                match = pattern.match(f"{word} {words[i+1][4]}")

            if match:
                ref_text = word
                rect = fitz.Rect(words[i][:4])
                j = i + 1

                # Look ahead for number part if not in current word
                while j < len(words) and j < i + 4:  # Look ahead up to 3 words
                    next_word = words[j][4]
                    combined_text = f"{ref_text} {next_word}"
                    if pattern.match(combined_text):
                        ref_text = combined_text
                        rect = rect.include_rect(fitz.Rect(words[j][:4]))
                        j += 1
                    else:
                        break

                return ref_type, ref_text, rect, j

        # Check for section references
        for pattern in self.patterns["section"]:
            match = pattern.match(word)
            if match:
                ref_text = word
                rect = fitz.Rect(words[i][:4])
                j = i + 1

                # Look ahead for additional parts
                while j < len(words) and j < i + 4:
                    next_word = words[j][4]
                    if re.match(r"^[0-9.]+$", next_word):
                        ref_text = f"{ref_text} {next_word}"
                        rect = rect.include_rect(fitz.Rect(words[j][:4]))
                        j += 1
                    else:
                        break

                return "section", ref_text, rect, j

        # Check for equation references
        for pattern in self.patterns["equation"]:
            match = pattern.match(word)
            if match:
                ref_text = word
                rect = fitz.Rect(words[i][:4])
                j = i + 1

                # Look ahead for additional parts
                while j < len(words) and j < i + 4:
                    next_word = words[j][4]
                    if (
                        "(" in next_word
                        or ")" in next_word
                        or re.match(r"^[0-9.-]+$", next_word)
                    ):
                        ref_text = f"{ref_text} {next_word}"
                        rect = rect.include_rect(fitz.Rect(words[j][:4]))
                        j += 1
                    else:
                        break

                return "equation", ref_text, rect, j

        return None, None, None, i + 1

    def find_all_references(self) -> Dict[str, List[Dict]]:
        """
        Find all references (figures, tables, sections, equations) in a single pass through the document.
        Returns a dictionary with lists of references by type.
        """
        references = {
            "figure": [],
            "table": [],
            "section": [],
            "equation": [],
            "equation_number": [],
        }

        # First find actual equation numbers in the document
        equation_numbers = self.find_equation_numbers()
        references["equation_number"].extend(equation_numbers)

        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            words = page.get_text("words")

            i = 0
            while i < len(words):
                ref_type, ref_text, rect, next_i = self._check_reference_match(words, i)

                if ref_type and not self._is_overlapping_with_existing(page_num, rect):
                    references[ref_type].append(
                        {
                            "type": ref_type,
                            "text": ref_text,
                            "page": page_num,
                            "rect": rect,
                        }
                    )

                i = next_i

        return references

    def create_annotations(
        self, references: Dict[str, List[Dict]], annotation_type: str = "highlight"
    ) -> None:
        """
        Create annotations for the found references.

        Args:
            references: Dictionary of references by type
            annotation_type: Type of annotation to create ('highlight' or 'link')
        """
        for ref_type, refs in references.items():
            for ref in refs:
                page = self.doc[ref["page"]]

                if annotation_type == "highlight":
                    annot = page.add_highlight_annot(ref["rect"])
                    annot.set_info(
                        title=f"{ref_type.capitalize()} Reference",
                        content=f"Reference to {ref['text']}",
                    )

                elif annotation_type == "link":
                    # For linking, you would need to determine the destination page
                    # This is a placeholder for link creation logic
                    dest_page = self._find_destination_page(ref)
                    if dest_page is not None:
                        page.insert_link(
                            {
                                "kind": fitz.LINK_GOTO,
                                "from": ref["rect"],
                                "to": fitz.Point(
                                    0, 0
                                ),  # Destination point on target page
                                "page": dest_page,
                            }
                        )

    def _find_destination_page(self, reference: Dict) -> Optional[int]:
        """
        Find the destination page for a reference.
        This is a placeholder method - actual implementation would depend on document structure.
        """
        # Implementation would need to search for the actual figure, table, etc.
        # and return its page number
        return None

    def close(self):
        """Close the PDF document."""
        self.doc.close()
