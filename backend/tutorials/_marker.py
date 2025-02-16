import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from marker.config.parser import ConfigParser
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import save_output
from marker.renderers.json import JSONOutput


def parse_args():
    # Set up and parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="Run a simple example of a marker, PDF parsing workflow."
    )
    parser.add_argument(
        "--file_path",
        type=str,
        default="assets/2501.00663v1.pdf",
        help="The path to the PDF file to be processed.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs/marker",
        help="The directory to save the output files.",
    )
    parser.add_argument(
        "--use_llm",
        action="store_true",
        help="Use the LLM model for processing.",
    )

    return parser.parse_args()


def main():
    # Parse arguments and load environment variables.
    args = parse_args()
    load_dotenv(os.path.expanduser("~/.env"))

    # Define basic configuration options.
    config = {
        "output_format": "json",
    }
    if args.use_llm:
        config.update(
            {
                "use_llm": True,
                "google_api_key": os.getenv("GOOGLE_API_KEY"),
            }
        )

    # Initialize configuration parser.
    config_parser = ConfigParser(config)
    file_path = Path(args.file_path)

    # Create a PDF converter with specified configuration, model dictionary,
    # processing steps, and renderer.
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=config_parser.get_processors(),
        renderer=config_parser.get_renderer(),
    )

    # Process the PDF file and generate rendered output.
    rendered = converter(str(file_path))
    rendered.metadata.update({"file_id": str(uuid4())})

    # Create the output directory using the file's stem for organization.
    output_dir = Path(args.output_dir) / file_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the rendered output to the output directory.
    fname_base = "res"
    save_output(rendered, output_dir, fname_base)

    # Load generated metadata and block outputs from the output directory.
    metadata_path = output_dir / f"{fname_base}_meta.json"
    block_outputs_path = output_dir / f"{fname_base}.json"

    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    with open(block_outputs_path, "r") as f:
        block_outputs = json.load(f)

    # Wrap the output using JSONOutput model and print it.
    output = JSONOutput(**block_outputs, metadata=metadata)


if __name__ == "__main__":
    main()
