import argparse
from pathlib import Path

import numpy as np
import pdf2image
from paddlex import create_model


def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "pdf_path",
        type=str,
        help="The path to the PDF document to process.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs/paddlex",
        help="The directory to save the output files.",
    )
    parser.add_argument(
        "--model_name",
        type=str,
        default="RT-DETR-H_layout_17cls",
        help="The name of the model to use",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=1,
        help="The batch size to use",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    filename_wo_ext = Path(args.pdf_path).stem
    output_dir = Path(args.output_dir) / filename_wo_ext
    model = create_model(args.model_name)
    images = pdf2image.convert_from_path(args.pdf_path)
    images = [np.array(image) for image in images]
    output = model.predict(images, batch_size=args.batch_size)
    for i, res in enumerate(output):
        res.save_to_img(output_dir / f"img_{i:03d}.png")
        res.save_to_json(output_dir / f"res_{i:03d}.json")


if __name__ == "__main__":
    main()
