from odmantic import Model


class Block(Model):
    """
    - block_type: [
        "Line", "Span", "FigureGroup", "TableGroup", "ListGroup", "PictureGroup", "Page", "Caption",
        "Code", "Figure", "Footnote", "Form", "Equation", "Handwriting", "TextInlineMath", "ListItem",
        "PageFooter", "PageHeader", "Picture", "SectionHeader", "Table", "Text", "TableOfContents", "Document"
    ]
    - section_hierarchy: indicates the sections that the block is part of. 1 indicates an h1 tag, 2 an h2, and so on.
    - images: base64 encoded images. The key will be the block id, and the data will be the encoded image.
    """

    file_id: str
    page_number: int
    block_id: str
    block_type: str
    html: str
    polygon: list[list[float]]
    bbox: list[float]
    children: list[str] | None = None
    # convert Marker's Dict[int, str] to Dict[str, str]
    section_hierarchy: dict[str, str] | None = None
    images: dict | None = None
