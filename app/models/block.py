from typing import Dict, List

from beanie import Document
from marker.renderers.json import JSONBlockOutput


def convert_keys_to_str(data):
    if isinstance(data, dict):
        return {str(key): convert_keys_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_str(item) for item in data]
    else:
        return data


class Block(Document):
    file_id: str
    page_number: int
    block_id: str
    block_type: str
    html: str
    polygon: List[List[float]]
    bbox: List[float]
    children: List[str] | None = None
    section_hierarchy: Dict[str, str] | None = None
    images: dict | None = None

    class Settings:
        name = "block"

    @staticmethod
    def from_JSONBlockOutput(
        file_id: str, page_number: int, json_block_output: JSONBlockOutput
    ) -> "Block":
        return Block(
            file_id=file_id,
            page_number=page_number,
            block_id=json_block_output.id,
            block_type=json_block_output.block_type,
            html=json_block_output.html,
            polygon=json_block_output.polygon,
            bbox=json_block_output.bbox,
            children=(
                [child.id for child in json_block_output.children]
                if json_block_output.children
                else None
            ),
            section_hierarchy=(
                convert_keys_to_str(json_block_output.section_hierarchy)
                if json_block_output.section_hierarchy
                else None
            ),
            images=json_block_output.images,
        )
