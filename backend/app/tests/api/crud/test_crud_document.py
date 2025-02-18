import io
from fastapi import UploadFile
from pathlib import Path
from starlette.datastructures import Headers

import pytest
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import document as crud_document
from app.schemas.document import DocumentCreate, DocumentUpdate


@pytest.mark.asyncio
async def test_create_document(pdf_path: Path, engine: AIOEngine) -> None:
    # Read the file bytes and prepare an UploadFile instance
    with open(pdf_path, "rb") as f:
        bytes_data = f.read()
    file = io.BytesIO(bytes_data)
    file.seek(0)
    headers = Headers({"content-type": "application/pdf"})
    upload_file = UploadFile(filename=pdf_path.name, file=file, headers=headers)
    document_in = DocumentCreate(
        name="name", content_type="application/pdf", file=upload_file
    )
    document = await crud_document.create(engine, obj_in=document_in)
    assert document.name == document_in.name
    assert (settings.DOCUMENT_DIR_PATH / document.path).exists()


@pytest.mark.asyncio
async def test_update_document(pdf_path: Path, engine: AIOEngine) -> None:
    # Create an UploadFile instance for the document creation
    with open(pdf_path, "rb") as f:
        bytes_data = f.read()
    file = io.BytesIO(bytes_data)
    file.seek(0)
    headers = Headers({"content-type": "application/pdf"})
    upload_file = UploadFile(filename=pdf_path.name, file=file, headers=headers)
    document_in = DocumentCreate(
        name="name", content_type="application/pdf", file=upload_file
    )
    document = await crud_document.create(engine, obj_in=document_in)

    document_in_update = DocumentUpdate(name="name updated")
    document_updated = await crud_document.update(
        engine, db_obj=document, obj_in=document_in_update
    )
    assert document_updated.name == document_in_update.name
