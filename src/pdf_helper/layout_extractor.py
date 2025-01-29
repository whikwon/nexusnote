"""
https://paddlepaddle.github.io/PaddleX/latest/en/module_usage/tutorials/ocr_modules/layout_detection.html
"""

import enum
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
from paddlex import create_model
from paddlex.inference.results.det import DetResult
from PIL import Image
from pydantic import BaseModel


class PaddleX17Cls(enum.Enum):
    """
    17 classes for PaddleX layout detection model.
    """

    paragraph_title = 0
    picture = 1
    text = 2
    number = 3
    abstract = 4
    content = 5
    chart_title = 6
    formula = 7
    table = 8
    table_title = 9
    reference = 10
    document_title = 11
    footnote = 12
    header = 13
    algorithm = 14
    footer = 15
    seal = 16


class PaddleXBox(BaseModel):
    cls_id: PaddleX17Cls
    label: str
    score: float
    coordinate: List[float]  # x1y1x2y2


class PaddleXResult(BaseModel):
    input_path: str | Path
    boxes: List[PaddleXBox]
    image_size: Tuple[int, int]  # (width, height)
    page_number: int


class LayoutExtractor:
    def __init__(self, model_name: str = "RT-DETR-H_layout_17cls"):
        self.model = create_model(model_name)

    def extract_layout(
        self,
        imgs: List[np.ndarray],
        page_numbers: List[int],
        batch_size: int = 1,
        save_dir: str = None,
    ) -> List[PaddleXResult]:
        output: List[DetResult] = list(self.model.predict(imgs, batch_size=batch_size))
        for res, page_num in zip(output, page_numbers):
            res["page_number"] = page_num
            res["boxes"] = sorted(res["boxes"], key=lambda x: x["coordinate"][1])
            res["image_size"] = Image.open(res["input_path"]).size

        if save_dir is not None:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            for i, res in enumerate(output):
                res.save_to_img(f"{save_dir}/img_{i:03d}.png")
                res.save_to_json(f"{save_dir}/res_{i:03d}.json")
        return [PaddleXResult(**res) for res in output]
