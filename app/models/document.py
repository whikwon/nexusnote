from typing import Any, Dict

from beanie import Document
from marker.renderers.json import JSONOutput


class Document(Document):
    file_id: str
    file_name: str
    metadata: Dict[str, Any]

    @staticmethod
    def from_JSONOutput(file_id: str, file_name: str, output: JSONOutput):
        return Document(
            file_id=file_id,
            file_name=file_name,
            metadata=output.metadata,
        )
