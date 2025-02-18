from io import BytesIO
from pathlib import Path
from fastapi import UploadFile
from starlette.datastructures import Headers
import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app import schemas
from app.core.config import settings
from app.crud import annotation as crud_annotation
from app.crud import concept as crud_concept
from app.crud import document as crud_document
from app.schemas.annotation import AnnotationCreate, HighlightArea


def test_upload_document(pdf_path: Path, client: TestClient) -> None:
    with open(pdf_path, "rb") as file:
        files = {"file": ("2501.00663v1.pdf", file, "application/pdf")}
        data = {"name": "assets/2501.00663v1.pdf", "content_type": "application/pdf"}
        res = client.post(
            f"{settings.API_V1_STR}/document/upload",
            data=data,
            files=files,
        )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_process_document(
    pdf_path: Path, engine: AIOEngine, client: TestClient
) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file = BytesIO(file_bytes)
    headers = Headers({"content-type": "application/pdf"})
    upload_file = UploadFile(filename=pdf_path.name, file=file, headers=headers)
    document = await crud_document.create(
        engine,
        obj_in=schemas.DocumentCreate(
            name="name", content_type="application/pdf", file=upload_file
        ),
    )

    res = client.post(
        f"{settings.API_V1_STR}/document/process",
        json={"id": document.id},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_delete_document(
    pdf_path: Path, engine: AIOEngine, client: TestClient
) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    file = BytesIO(file_bytes)
    headers = Headers({"content-type": "application/pdf"})
    upload_file = UploadFile(filename=pdf_path.name, file=file, headers=headers)
    document = await crud_document.create(
        engine,
        obj_in=schemas.DocumentCreate(
            name="name", content_type="application/pdf", file=upload_file
        ),
    )
    highlight_area = HighlightArea(
        height=100, left=100, pageIndex=1, top=100, width=100
    )
    annotation = await crud_annotation.create(
        engine,
        obj_in=AnnotationCreate(
            file_id=document.id,
            comment="comment",
            quote="quote",
            highlight_areas=[highlight_area],
        ),
    )
    concept = await crud_concept.create(
        engine,
        obj_in=schemas.ConceptCreate(
            name="concept", comment="comment", annotation_ids=[annotation.id]
        ),
    )

    res = client.post(
        f"{settings.API_V1_STR}/document/delete",
        json={"id": document.id},
    )
    assert res.status_code == 200
    assert await crud_document.get(engine, document.id) is None
    assert await crud_annotation.get(engine, annotation.id) is None
    concept = await crud_concept.get(engine, concept.id)
    assert concept.annotation_ids == []
