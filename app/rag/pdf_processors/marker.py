import json
from pathlib import Path
from typing import List, Union

from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.renderers.json import JSONBlockOutput, JSONOutput
from marker.settings import settings


class MarkerPDFProcessor:
    default_config = {
        "output_format": "json",
    }

    def __init__(self, config: dict = None):
        if config is None:
            config = MarkerPDFProcessor.default_config
        self.config_parser = ConfigParser(config)
        self.converter = PdfConverter(
            config=self.config_parser.generate_config_dict(),
            artifact_dict=create_model_dict(),
            processor_list=self.config_parser.get_processors(),
            renderer=self.config_parser.get_renderer(),
        )

    def _extract_rendered_json_data(self, rendered):
        text, _, _ = text_from_rendered(rendered)
        text = text.encode(settings.OUTPUT_ENCODING, errors="replace").decode(
            settings.OUTPUT_ENCODING
        )
        children = json.loads(text)["children"]
        return {
            "children": children,
            "block_type": rendered.block_type,
            "metadata": rendered.metadata,
        }

    def process(self, pdf_path: Union[str | Path]):
        if isinstance(pdf_path, Path):
            pdf_path = str(pdf_path)
        rendered = self.converter(pdf_path)
        if isinstance(rendered, JSONOutput):
            return JSONOutput(**self._extract_rendered_json_data(rendered))
        return rendered


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
