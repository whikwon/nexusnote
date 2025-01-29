# Description: Extract contents from a PDF file

import argparse
from pathlib import Path

import fitz
from gmft.auto import AutoTableDetector, AutoTableFormatter
from gmft.pdf_bindings import PyPDFium2Document

from src.pdf_helper.content_extractor import chunk_pages


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
    detector = AutoTableDetector()
    output_dir = Path(args.output_dir) / Path(args.pdf_path).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = PyPDFium2Document(args.pdf_path)
    tables_per_page = []
    for page in doc:
        tables_per_page.append(detector.extract(page))

    doc = fitz.open(args.pdf_path)
    toc = doc.get_toc()

    # get all chunks
    all_chunks = chunk_pages(doc, tables_per_page)
    for i, chunk in enumerate(all_chunks):
        with open(output_dir / f"chunk_{i:03d}.txt", "w") as f:
            f.write(chunk)

    # get chunks for each section
    lvl_1_chunks = []
    lvl_1_toc = [i for i in toc if i[0] == 1]

    # assume that there is no duplication in page_num in lvl_1_toc
    for i, (lvl_1, title, page_num) in enumerate(lvl_1_toc):
        start_page = page_num
        if i + 1 < len(lvl_1_toc):
            end_page = lvl_1_toc[i + 1][2]
        else:
            end_page = len(doc)

        lvl_1_chunks.append(
            chunk_pages(
                doc[start_page - 1 : end_page],
                tables_per_page[start_page - 1 : end_page],
                chunk_size=1000_1000,
            )
        )
    for lvl, chunks in enumerate(lvl_1_chunks):
        for i, chunk in enumerate(chunks):
            with open(output_dir / f"lvl_1_chunk_{lvl:02d}_{i:02d}.txt", "w") as f:
                f.write(chunk)


if __name__ == "__main__":
    main()
