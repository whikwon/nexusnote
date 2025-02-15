from typing import List

from bs4 import BeautifulSoup
from langchain_core.documents import Document
from pydantic import BaseModel

from app.schemas import BlockBase

from .chunk import ChunkMetadata


class SectionBase(BaseModel):
    file_id: str
    section_hierarchy: dict[str, str]
    blocks: list[BlockBase]

    @staticmethod
    def from_blocks(
        blocks: list[BlockBase], section_hierarchy: dict[str, str]
    ) -> "SectionBase":
        """
        Create a section from a list of blocks
        """
        file_id = blocks[0].file_id
        section_blocks = []
        for block in blocks:
            if (
                block.section_hierarchy is not None
                and section_hierarchy.items() <= block.section_hierarchy.items()
            ):
                section_blocks.append(block)
        return SectionBase(
            file_id=file_id,
            section_hierarchy=section_hierarchy,
            blocks=section_blocks,
        )

    def to_chunks(self, embedding_model, size_limit=None) -> List[Document]:
        """
        Convert the section into chunks
        """
        i = 0
        text = ""
        block_ids = []
        for block in self.blocks:
            if block.block_type.lower().startswith("table"):
                text += block.html.strip() + "\n"
            else:
                soup = BeautifulSoup(block.html, "html.parser")
                text += soup.get_text(separator=" ", strip=True) + "\n"
            block_ids.append(block.block_id)

        metadata = ChunkMetadata(
            file_id=self.file_id,
            section_hierarchy=self.section_hierarchy,
            chunk_id=i,
            block_ids=block_ids,
            embedding_model=embedding_model,
        )
        page_content = text
        chunk = Document(metadata=metadata.model_dump(), page_content=page_content)
        return [chunk]


def gather_section_hierarchies(
    blocks: list[BlockBase], levels: list[str]
) -> list[dict[str, str]]:
    required_keys = set(levels)
    seen = set()  # to store frozenset representations for deduplication
    results = []

    for block in blocks:
        section_hierarchy = block.section_hierarchy
        if not section_hierarchy:
            continue
        # Check if all required levels exist in the current section_hierarchy
        if required_keys <= section_hierarchy.keys():
            # Build a new dictionary with just the desired levels
            sub_hierarchy = {lvl: section_hierarchy[lvl] for lvl in levels}
            # Convert to a frozenset so it can be added to a set for deduplication
            key = frozenset(sub_hierarchy.items())
            if key not in seen:
                seen.add(key)
                results.append(sub_hierarchy)

    return results
