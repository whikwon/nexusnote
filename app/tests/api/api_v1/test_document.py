import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import document as crud_document
from app.schemas.document import DocumentCreate


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
    document_in = DocumentCreate(name="name", content=content)
    document = await crud_document.create(engine, obj_in=document_in)

    res = client.post(
        f"{settings.API_V1_STR}/document/process",
        json={"id": document.id},
    )
    assert res.status_code == 200
