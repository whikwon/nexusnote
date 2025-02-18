import io
from pathlib import Path
from fastapi import UploadFile
from starlette.datastructures import Headers

import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import annotation as crud_annotation
from app.crud import document as crud_document
from app.schemas.annotation import AnnotationCreate, HighlightArea
from app.schemas.document import DocumentCreate


@pytest.mark.asyncio
async def test_create_annotation(pdf_path: Path, engine: AIOEngine, client: TestClient):
    with open(pdf_path, "rb") as f:
        bytes_data = f.read()
    file = io.BytesIO(bytes_data)
    file.seek(0)
    headers = Headers({"content-type": "application/pdf"})
    upload_file = UploadFile(filename=pdf_path.name, file=file, headers=headers)
    document = await crud_document.create(
        engine,
        obj_in=DocumentCreate(
            name="name", content_type="application/pdf", file=upload_file
        ),
    )

    res = client.post(
        f"{settings.API_V1_STR}/annotation/create",
        json={
            "file_id": document.id,
            "quote": "quote",
            "comment": "comment",
            "highlight_areas": [
                {
                    "height": 100,
                    "left": 100,
                    "pageIndex": 1,
                    "top": 100,
                    "width": 100,
                }
            ],
        },
    )
    assert res.status_code == 200
    annotation = res.json()
    assert "id" in annotation
    assert annotation["file_id"] == document.id
    assert annotation["quote"] == "quote"
    assert annotation["comment"] == "comment"
    assert len(annotation["highlight_areas"]) == 1
    assert annotation["highlight_areas"][0]["height"] == 100
    assert annotation["highlight_areas"][0]["left"] == 100
    assert annotation["highlight_areas"][0]["pageIndex"] == 1
    assert annotation["highlight_areas"][0]["top"] == 100
    assert annotation["highlight_areas"][0]["width"] == 100


@pytest.mark.asyncio
async def test_update_annotation(engine: AIOEngine, client: TestClient):
    annotation = await crud_annotation.create(
        engine,
        obj_in=AnnotationCreate(
            file_id="file_id",
            quote="quote",
            comment="comment",
            highlight_areas=[
                HighlightArea(height=100, left=100, pageIndex=1, top=100, width=100)
            ],
        ),
    )

    res = client.post(
        f"{settings.API_V1_STR}/annotation/update",
        json={"id": annotation.id, "comment": "comment updated"},
    )
    assert res.status_code == 200
    annotation_updated = res.json()
    assert annotation_updated["id"] == annotation.id
    assert annotation_updated["file_id"] == "file_id"
    assert annotation_updated["quote"] == "quote"
    assert annotation_updated["comment"] == "comment updated"
    assert len(annotation_updated["highlight_areas"]) == 1
    assert annotation_updated["highlight_areas"][0]["height"] == 100
    assert annotation_updated["highlight_areas"][0]["left"] == 100
    assert annotation_updated["highlight_areas"][0]["pageIndex"] == 1
    assert annotation_updated["highlight_areas"][0]["top"] == 100
    assert annotation_updated["highlight_areas"][0]["width"] == 100
