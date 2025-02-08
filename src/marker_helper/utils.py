import json

from marker.output import text_from_rendered
from marker.renderers.json import JSONOutput
from marker.settings import settings


def encode_marker_json_output(json_output: JSONOutput):
    text, _, _ = text_from_rendered(json_output)
    text = text.encode(settings.OUTPUT_ENCODING, errors="replace").decode(
        settings.OUTPUT_ENCODING
    )
    children = json.loads(text)
    block_type = json_output.block_type
    metadata = json_output.metadata

    return {
        "children": children,
        "block_type": block_type,
        "metadata": metadata,
    }
