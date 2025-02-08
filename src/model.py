from typing import Any, Dict, List, Optional

from marker.renderers.json import JSONBlockOutput, JSONOutput
from pydantic import BaseModel


def convert_keys_to_str(data):
    if isinstance(data, dict):
        return {str(key): convert_keys_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_keys_to_str(item) for item in data]
    else:
        return data


class Page(BaseModel):
    file_id: str
    page_number: int
    json_block_output: JSONBlockOutput

    @staticmethod
    def get_pages_from_json_output(
        file_id: str, json_output: JSONOutput
    ) -> List["Page"]:
        """
        Generate a list of Page instances from a JSONOutput instance.
        """
        return [
            Page(
                file_id=file_id,
                page_number=i,
                json_block_output=child,
            )
            for i, child in enumerate(json_output.children)
        ]

    @staticmethod
    def _convert_section_hierarchy_keys_to_str(data: dict) -> dict:
        """
        Recursively convert keys of section_hierarchy from int to str.
        """
        if "section_hierarchy" in data and data["section_hierarchy"] is not None:
            data["section_hierarchy"] = {
                str(k): v for k, v in data["section_hierarchy"].items()
            }
        if "children" in data and data["children"] is not None:
            data["children"] = [
                Page._convert_section_hierarchy_keys_to_str(child)
                for child in data["children"]
            ]
        return data

    @staticmethod
    def _convert_section_hierarchy_keys_to_int(data: dict) -> dict:
        """
        Recursively convert keys of section_hierarchy from str back to int.
        """
        if "section_hierarchy" in data and data["section_hierarchy"] is not None:
            data["section_hierarchy"] = {
                int(k): v for k, v in data["section_hierarchy"].items()
            }
        if "children" in data and data["children"] is not None:
            data["children"] = [
                Page._convert_section_hierarchy_keys_to_int(child)
                for child in data["children"]
            ]
        return data

    def to_mongo(self) -> dict:
        """
        Convert the Page instance to a MongoDB-friendly dictionary.
        This method converts the keys of the section_hierarchy in the nested json_block_output
        (and its children) from integers to strings.
        """
        data = self.model_dump()
        # Process the nested json_block_output dictionary for section_hierarchy conversion.
        data["json_block_output"] = Page._convert_section_hierarchy_keys_to_str(
            self.json_block_output.model_dump()
        )
        return data

    @classmethod
    def from_mongo(cls, data: dict) -> "Page":
        """
        Create a Page instance from a MongoDB-friendly dictionary.
        This method converts the keys of the section_hierarchy in the nested json_block_output
        (and its children) from strings back to integers.
        """
        if "json_block_output" in data:
            # Convert section_hierarchy keys from str back to int in the json_block_output dictionary.
            converted = Page._convert_section_hierarchy_keys_to_int(
                data["json_block_output"]
            )
            # Use JSONBlockOutput.parse_obj instead of BaseModel.parse_obj
            data["json_block_output"] = JSONBlockOutput.parse_obj(converted)
        return cls(**data)


class Document(BaseModel):
    file_id: str
    file_name: str
    metadata: Dict[str, Any]


class MarkerJSONOutput(JSONOutput):
    def get_document(self, file_id: str, file_name: str) -> Document:
        """
        Generate a Document instance from the MarkerJSONOutput.
        """
        return Document(
            file_id=file_id,
            file_name=file_name,
            metadata=self.metadata,
        )

    def get_pages(self, file_id: str) -> List[Page]:
        """
        Generate a list of Page instances from the MarkerJSONOutput.
        """
        return [
            Page(
                file_id=file_id,
                page_number=page_number,
                json_block_output=page,
            )
            for page_number, page in enumerate(self.children)
        ]
