import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import annotation as crud_annotation
from app.crud import document as crud_document
from app.schemas.annotation import AnnotationCreate
from app.schemas.document import DocumentCreate


@pytest.mark.asyncio
async def test_create_annotation(pdf_path: Path, engine: AIOEngine, client: TestClient):
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    content = base64.b64encode(file_bytes).decode("utf-8")
    document_in = DocumentCreate(name="name", content=content)
    document = await crud_document.create(engine, obj_in=document_in)

    res = client.post(
        f"{settings.API_V1_STR}/annotation/create",
        json={"file_id": document.id, "page_number": 0, "comment": "comment"},
    )
    assert res.status_code == 200
    annotation = res.json()
    assert "id" in annotation
    assert annotation["file_id"] == document.id
    assert annotation["page_number"] == 0
    assert annotation["comment"] == "comment"


@pytest.mark.asyncio
async def test_update_annotation(engine: AIOEngine, client: TestClient):
    annotation_in = AnnotationCreate(
        file_id="file_id", page_number=0, comment="comment"
    )
    annotation = await crud_annotation.create(engine, obj_in=annotation_in)

    res = client.post(
        f"{settings.API_V1_STR}/annotation/update",
        json={"id": annotation.id, "comment": "comment updated"},
    )
    assert res.status_code == 200
    annotation_updated = res.json()
    assert annotation.id == annotation_updated["id"]
    assert annotation["file_id"] == "file_id"
    assert annotation["page_number"] == 0
    assert annotation["comment"] == "comment updated"
