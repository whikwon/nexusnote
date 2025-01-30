# Description: Extract contents from a PDF file

import argparse
from pathlib import Path

import fitz

from src.pdf_helper.content_extractor import chunk_layout_contents, parse_box_contents
from src.pdf_helper.content_linker import process_document_relationships
from src.pdf_helper.layout_extractor import LayoutExtractor, PaddleX17Cls
from src.utils.image import fitz_page_to_image_array
from src.utils.visualize import visualize_pdf_contents


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
        default="./outputs/extract_contents",
        help="The directory to save the output files.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    output_dir = Path(args.output_dir) / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    images = [fitz_page_to_image_array(page) for page in doc]
    layout_extractor = LayoutExtractor()
    output = layout_extractor.extract_layout(
        images, list(range(1, len(images) + 1)), batch_size=2
    )

    page = doc[0]
    content_list = []

    for page_num, res in enumerate(output):
        page = doc[page_num]
        pdf_width, pdf_height = page.rect.width, page.rect.height
        img_width, img_height = res.image_size
        w_scale = pdf_width / img_width
        h_scale = pdf_height / img_height
        for box in res.boxes:
            content = parse_box_contents(page, box, w_scale, h_scale)
            content_list.append(content)

    content_list = process_document_relationships(content_list)
    chunks = chunk_layout_contents(
        content_list,
        content_filter_func=lambda x: x.cls_id
        not in [
            PaddleX17Cls.number,
            PaddleX17Cls.picture,
            PaddleX17Cls.table,
            PaddleX17Cls.algorithm,
            PaddleX17Cls.formula,
        ],
        overlap_boxes=1,
    )
    visualize_pdf_contents(
        pdf_path, content_list, chunks, output_dir / "visualized_pdf.pdf"
    )


if __name__ == "__main__":
    main()
