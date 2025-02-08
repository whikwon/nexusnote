from typing import List, Optional

from bs4 import BeautifulSoup
from langchain_core.documents import Document as langchain_Document
from marker.renderers.json import JSONBlockOutput, JSONOutput


def process_block(block: JSONBlockOutput) -> str:
    """
    Process the HTML content for a block based on its type.

    - If the block's type starts with "table" (e.g. "TableGroup", "Table"),
      preserve the original HTML.
    - Otherwise, if the HTML contains a table tag (as a fallback), also preserve the HTML.
    - Else, convert the HTML to plain text.
    """
    # Check if the block is table-related based on its block_type.
    if block.block_type.lower().startswith("table"):
        return block.html.strip()
    # For non-table content, strip out HTML tags.
    soup = BeautifulSoup(block.html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def flatten_blocks(blocks: List[JSONBlockOutput]) -> List[JSONBlockOutput]:
    """
    Recursively traverse the list of JSONBlockOutput blocks and return a flat list,
    preserving the order.
    """
    flat_list = []
    for block in blocks:
        flat_list.append(block)
        if block.children:
            flat_list.extend(flatten_blocks(block.children))
    return flat_list


def create_chunks_by_level(
    json_output: JSONOutput, file_id: str, desired_level: int
) -> List[langchain_Document]:
    """
    Create chunks grouped by a specified section/chapter level.

    For each block in the flattened structure, if its section_hierarchy indicates a header
    at the desired level, it marks the beginning of a new chunk. For each block,
    the content is processed by `process_block` so that table-related blocks are kept as HTML,
    while other blocks have their HTML stripped to plain text.

    Parameters:
        json_output: An instance of JSONOutput (the Marker output).
        desired_level: The section/chapter level used for chunking (e.g., 1 for section-level).

    Returns:
        A list of dictionaries, each with:
          - "section": an identifier for the chunk (or "default" if none),
          - "text": the concatenated content of that chunk.
    """
    flat_blocks = flatten_blocks(json_output.children)

    chunks = []
    current_section: Optional[str] = None
    current_texts: List[str] = []

    for block in flat_blocks:
        # Determine if this block is associated with a new section at the desired level.
        section_id = None
        if block.section_hierarchy and desired_level in block.section_hierarchy:
            section_id = block.section_hierarchy[desired_level]

        # If a new section is encountered, finalize the previous chunk.
        if section_id is not None and section_id != current_section:
            if current_texts:
                chunk_text = "\n".join(current_texts).strip()
                chunks.append(
                    langchain_Document(
                        metadata={
                            "file_id": file_id,
                            "section": (
                                current_section
                                if current_section is not None
                                else "default"
                            ),
                        },
                        page_content=chunk_text,
                    )
                )
                current_texts = []
            current_section = section_id

        # Use a default section name if none is set.
        if current_section is None:
            current_section = "default"

        # Process the block's content.
        processed_content = process_block(block)
        if processed_content:
            current_texts.append(processed_content)

    # Append any remaining text as the final chunk.
    if current_texts:
        chunk_text = "\n".join(current_texts).strip()
        chunks.append(
            langchain_Document(
                metadata={
                    "file_id": file_id,
                    "section": (
                        current_section if current_section is not None else "default"
                    ),
                },
                page_content=chunk_text,
            )
        )

    return chunks
