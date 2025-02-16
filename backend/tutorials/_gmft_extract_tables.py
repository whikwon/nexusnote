"""
https://github.com/conjuncts/gmft/blob/main/notebooks/quickstart.ipynb

Because the table has an unstructured format, various methods are needed for extraction. gmft provides a high-performance method.
"""

import argparse
from pathlib import Path

from gmft.auto import AutoTableDetector, AutoTableFormatter
from gmft.pdf_bindings import PyPDFium2Document


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
        default="./outputs/gmft",
        help="The directory to save the output files.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    detector = AutoTableDetector()
    formatter = AutoTableFormatter()
    output_dir = Path(args.output_dir) / Path(args.pdf_path).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    def ingest_pdf(pdf_path):  # produces list[CroppedTable]
        doc = PyPDFium2Document(pdf_path)
        tables = []
        for page in doc:
            tables += detector.extract(page)
        return tables, doc

    tables, doc = ingest_pdf(args.pdf_path)
    for i, table in enumerate(tables):
        confidence_score = table.confidence_score
        if confidence_score > 0.99:
            ft = formatter.extract(table)
            df = ft.df()
            captions = ft.captions()
            csv_output_path = output_dir / f"table_contents_{i:03d}.csv"
            df.to_csv(csv_output_path, index=False)
            captions_output_path = output_dir / f"table_captions_{i:03d}.txt"
            with open(captions_output_path, "w") as f:
                f.write("\n".join(captions))

    doc.close()  # once you're done with the document


if __name__ == "__main__":
    main()
