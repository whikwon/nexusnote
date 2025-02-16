import argparse
import io
import json
from pathlib import Path
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
from pydantic import BaseModel, Field
from tqdm import tqdm


class FitzPageImage(BaseModel):
    # https://pymupdf.readthedocs.io/en/latest/document.html#Document.get_page_images
    image_data: Tuple[int, int, int, int, int, str, str, str, str, int]

    @property
    def xref(self) -> int:
        return self.image_data[0]

    @property
    def smask(self) -> int:
        return self.image_data[1]

    @property
    def width(self) -> int:
        return self.image_data[2]

    @property
    def height(self) -> int:
        return self.image_data[3]

    @property
    def bpc(self) -> int:
        return self.image_data[4]

    @property
    def colorspace(self) -> str:
        return self.image_data[5]

    @property
    def alt_colorspace(self) -> str:
        return self.image_data[6]

    @property
    def name(self) -> str:
        return self.image_data[7]

    @property
    def filter(self) -> str:
        return self.image_data[8]

    @property
    def referencer(self) -> int:
        return self.image_data[9]


class FitzImage(BaseModel):
    # https://pymupdf.readthedocs.io/en/latest/document.html#Document.extract_image
    ext: str
    smask: int
    width: int
    height: int
    colorspace: int
    bpc: int
    xres: int
    yres: int
    cs_name: str = Field(alias="cs-name")
    image: bytes


class BBoxModel(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def from_fitz_rect(cls, rect: fitz.Rect) -> "BBoxModel":
        return cls(x0=rect.x0, y0=rect.y0, x1=rect.x1, y1=rect.y1)

    def to_fitz_rect(self) -> fitz.Rect:
        return fitz.Rect(self.x0, self.y0, self.x1, self.y1)


class PointModel(BaseModel):
    x: float
    y: float

    @classmethod
    def from_fitz_point(cls, point: fitz.Point) -> "PointModel":
        return cls(x=point.x, y=point.y)

    def to_fitz_point(self) -> fitz.Point:
        return fitz.Point(self.x, self.y)


class FitzLink(BaseModel):
    # https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
    kind: int  # https://pymupdf.readthedocs.io/en/latest/vars.html#linkdest-kinds
    xref: int
    from_rect: BBoxModel = Field(alias="from")
    page: Optional[int] = None
    to: Optional[PointModel] = None
    file: Optional[str] = None
    uri: Optional[str] = None
    nameddest: Optional[str] = None
    zoom: Optional[float] = None
    id: str


class ImageCaptionData(BaseModel):
    image: FitzImage
    image_bbox: BBoxModel
    caption: str


class FitzBlock(BaseModel):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="PyMuPDF Extract Images with Caption, Links, and Table of Contents"
    )
    parser.add_argument(
        "pdf_path",
        type=str,
        help="The path to the PDF document to process.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs/pymupdf",
    )
    return parser.parse_args()


VERTICAL_MARGIN = 40  # Adjust this value based on your PDF layout


def get_adjusted_bbox(
    bbox: fitz.Rect, page_num: int, curr_page_num: int, doc: fitz.Document
) -> fitz.Rect:
    if page_num == curr_page_num:
        return bbox

    adjusted_bbox = fitz.Rect(bbox)
    page_height = doc[curr_page_num].rect.height

    if page_num < curr_page_num:
        adjusted_bbox.y0 -= page_height
        adjusted_bbox.y1 -= page_height
    else:
        adjusted_bbox.y0 += page_height
        adjusted_bbox.y1 += page_height

    return adjusted_bbox


def extract_caption(
    doc: fitz.Document, curr_page_num: int, fitz_bbox: fitz.Rect, vertical_margin: float
) -> str:
    caption = ""

    for page_num in [curr_page_num, curr_page_num - 1, curr_page_num + 1]:
        if 0 <= page_num < len(doc):
            page = doc[page_num]
            text_blocks = page.get_text("dict")["blocks"]
            adjusted_image_bbox = get_adjusted_bbox(
                fitz_bbox, curr_page_num, page_num, doc
            )

            for block in text_blocks:
                block_bbox = fitz.Rect(block["bbox"])

                is_below = (
                    abs(block_bbox.y0 - adjusted_image_bbox.y1) < vertical_margin
                    and block_bbox.x0 >= adjusted_image_bbox.x0 - vertical_margin
                    and block_bbox.x1 <= adjusted_image_bbox.x1 + vertical_margin
                )
                is_above = (
                    abs(block_bbox.y1 - adjusted_image_bbox.y0) < vertical_margin
                    and block_bbox.x0 >= adjusted_image_bbox.x0 - vertical_margin
                    and block_bbox.x1 <= adjusted_image_bbox.x1 + vertical_margin
                )

                if is_below or is_above:
                    text = "".join(
                        span["text"]
                        for line in block["lines"]
                        for span in line["spans"]
                    )
                    lower_text = text.lower()
                    caption_starts = [
                        "figure",
                        "fig.",
                        "fig",
                        "image",
                        "photo",
                        "illustration",
                    ]

                    if any(lower_text.startswith(start) for start in caption_starts):
                        print(lower_text)
                        return text.strip()
                    elif not caption:
                        caption = text.strip()

            if caption:
                break

    return caption


def main():
    args = parse_args()
    output_dir = Path(args.output_dir) / Path(args.pdf_path).stem
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(args.pdf_path)
    # https://pymupdf.readthedocs.io/en/latest/document.html#Document.get_toc
    toc = doc.get_toc()  # lvl, title, page_num
    all_links = []
    all_image_caption_data = []
    for page_num, page in tqdm(
        enumerate(doc), desc="Extracting Images and Captions", total=len(doc)
    ):
        text = page.get_text()
        page_images: List[FitzPageImage] = [
            FitzPageImage(image_data=image) for image in page.get_images(full=True)
        ]

        for fitz_page_image in page_images:
            fitz_image = FitzImage(**doc.extract_image(fitz_page_image.xref))
            fitz_bbox: fitz.Rect = page.get_image_bbox(fitz_page_image.image_data)

            caption = extract_caption(doc, page_num, fitz_bbox, VERTICAL_MARGIN)

            all_image_caption_data.append(
                ImageCaptionData(
                    image=fitz_image,
                    image_bbox=BBoxModel.from_fitz_rect(fitz_bbox),
                    caption=caption,
                )
            )

        links = page.get_links()
        for link in links:
            link["from"] = BBoxModel.from_fitz_rect(link["from"])
            to = link.get("to")
            if to is not None:
                link["to"] = PointModel.from_fitz_point(to)
        all_links += [FitzLink(**link) for link in links]

    with open(output_dir / "toc.json", "w") as f:
        json.dump(toc, f, indent=4)

    with open(output_dir / "links.json", "w") as f:
        json.dump([link.model_dump(by_alias=True) for link in all_links], f, indent=4)

    # Replace the final image saving loop with this:
    for i, image_caption_data in enumerate(all_image_caption_data):
        image_bytes = io.BytesIO(image_caption_data.image.image)
        image = Image.open(image_bytes)
        image.save(output_dir / f"image_{i:03d}.{image_caption_data.image.ext}")

        with open(output_dir / f"image_caption_{i:03d}.txt", "w") as f:
            f.write(image_caption_data.caption)


if __name__ == "__main__":
    main()
