import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app import schemas
from app.core.config import settings
from app.crud import annotation as crud_annotation
from app.crud import concept as crud_concept
from app.crud import document as crud_document


def test_upload_document(pdf_path: Path, client: TestClient) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    content = base64.b64encode(file_bytes).decode("utf-8")
    res = client.post(
        f"{settings.API_V1_STR}/document/upload",
        json={"name": "assets/2501.00663v1.pdf", "content": content},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_process_document(
    pdf_path: str, engine: AIOEngine, client: TestClient
) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    content = base64.b64encode(file_bytes).decode("utf-8")
    document = await crud_document.create(
        engine, obj_in=schemas.DocumentCreate(name="name", content=content)
    )

    res = client.post(
        f"{settings.API_V1_STR}/document/process",
        json={"id": document.id},
    )
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_delete_document(
    pdf_path: str, engine: AIOEngine, client: TestClient
) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    content = base64.b64encode(file_bytes).decode("utf-8")
    document = await crud_document.create(
        engine, obj_in=schemas.DocumentCreate(name="name", content=content)
    )
    annotation = await crud_annotation.create(
        engine,
        obj_in=schemas.AnnotationCreate(
            file_id=document.id, page_number=0, comment="comment"
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
