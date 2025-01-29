"""
https://github.com/jsvine/pdfplumber
https://github.com/jsvine/pdfplumber/issues/318

The performance of table extraction is not high, and captions are not extracted during image and table extraction, so we decided to use a different library.
"""

import argparse
from pathlib import Path

import pdfplumber
from pdfplumber.utils import obj_to_bbox


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
        default="./outputs/pdfplumber",
        help="The directory to save the output files.",
    )
    return parser.parse_args()


COLORS = {
    "IMG_BBOX_STROKE": (255, 0, 0),
    "ANNOT_BBOX_STROKE": (0, 255, 0),
    "TABLE_BBOX_STROKE": (0, 0, 255),
    "HYPERLINK_BBOX_STROKE": (0, 255, 255),
}


def main():
    args = parse_args()
    output_dir = Path(args.output_dir) / Path(args.pdf_path).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(args.pdf_path) as pdf:
        for page in pdf.pages:
            img = page.to_image()

            for img_obj in page.images:
                img_bbox = obj_to_bbox(img_obj)
                img.draw_rect(
                    img_bbox,
                    fill=None,
                    stroke=COLORS["IMG_BBOX_STROKE"],
                    stroke_width=2,
                )

            for annot_obj in page.annots:
                annot_bbox = obj_to_bbox(annot_obj)
                img.draw_rect(
                    annot_bbox,
                    fill=None,
                    stroke=COLORS["ANNOT_BBOX_STROKE"],
                    stroke_width=2,
                )

            for table_obj in page.find_tables():
                img.draw_rect(
                    table_obj.bbox,
                    fill=None,
                    stroke=COLORS["TABLE_BBOX_STROKE"],
                    stroke_width=2,
                )

            for hyperlink_obj in page.hyperlinks:
                hyperlink_bbox = obj_to_bbox(hyperlink_obj)
                img.draw_rect(
                    hyperlink_bbox,
                    fill=None,
                    stroke=COLORS["HYPERLINK_BBOX_STROKE"],
                    stroke_width=2,
                )

            img.save(output_dir / f"{page.page_number:04d}.png")


if __name__ == "__main__":
    main()
