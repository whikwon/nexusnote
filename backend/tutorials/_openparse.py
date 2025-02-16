"""
https://github.com/Filimoa/open-parse

uuid 자동 생성
chunk 기능
"""

import argparse

import openparse


def parse_args():
    parser = argparse.ArgumentParser(description="open-parse example.")
    parser.add_argument(
        "pdf_path",
        type=str,
        help="The path to the PDF document to process.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs/openparse",
        help="The directory to save the output files.",
    )
    return parser.parse_args()


def main():
    basic_doc_path = "./assets/2501.00663v1.pdf"
    parser = openparse.DocumentParser(
        table_args={"parsing_algorithm": "pymupdf", "table_output_format": "markdown"},
    )
    parsed_basic_doc = parser.parse(basic_doc_path)

    for node in parsed_basic_doc.nodes:
        if "table" in node.variant:
            print("table")
        print(node)
