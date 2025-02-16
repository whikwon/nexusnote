import base64
from pathlib import Path

import pytest
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import document as crud_document
from app.schemas.document import DocumentCreate, DocumentUpdate


@pytest.mark.asyncio
async def test_create_document(pdf_path: Path, engine: AIOEngine) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    content = base64.b64encode(file_bytes).decode("utf-8")
    document_in = DocumentCreate(name="name", content=content)
    document = await crud_document.create(engine, obj_in=document_in)
    assert document.name == document_in.name
    assert (settings.DOCUMENT_DIR_PATH / document.path).exists()


@pytest.mark.asyncio
async def test_update_document(pdf_path: Path, engine: AIOEngine) -> None:
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    content = base64.b64encode(file_bytes).decode("utf-8")
    document_in = DocumentCreate(name="name", content=content)
    document = await crud_document.create(engine, obj_in=document_in)

    document_in_update = DocumentUpdate(name="name updated")
    document_updated = await crud_document.update(
        engine, db_obj=document, obj_in=document_in_update
    )
    assert document_updated.name == document_in_update.name
