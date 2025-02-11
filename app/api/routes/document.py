import base64
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request

from app.core.config import settings
from app.models import Block, Document
from app.rag.pdf_processors.marker import MarkerPDFProcessor, flatten_blocks
from app.schemas.request import PDFAddRequest, PDFProcessRequest
from app.schemas.section import Section, gather_section_hierarchies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doc", tags=["doc"])


@router.post("/extract")
async def extract_document(request: Request, payload: PDFProcessRequest):
    app_state = request.app.state
    vector_store = app_state.vector_store
    file_id = payload.file_id

    res = await Document.find_one({"file_id": file_id})
    if res is None:
        return {
            "status": "success",
            "message": "File not found in DB. Please add the file first.",
        }

    file_path = res.file_path
    file_name = res.file_name
    pdf_path = settings.DOCUMENT_DIR_PATH / file_path
    logger.info(f"Starting PDF processing for file: {file_name}({file_id})")

    pdf_processor = MarkerPDFProcessor({"output_format": "json"})
    logging.info("Initialized Marker PDF processor.")

    rendered = pdf_processor.process(pdf_path)
    blocks = flatten_blocks(rendered.children)
    blocks = [
        Block.from_JSONBlockOutput(file_id, page_number, block)
        for page_number, block in blocks
    ]
    Block.insert_many(blocks)

    section_hierarchies = gather_section_hierarchies(blocks, ["1", "2"])
    sections = [
        Section.from_blocks(blocks, section_hierarchy)
        for section_hierarchy in section_hierarchies
    ]
    chunks = [section.to_chunks()[0] for section in sections]
    logging.info(f"Created {len(chunks)} chunks from the document.")

    document_ids = vector_store.add_documents(chunks)
    logging.info(f"Added {len(document_ids)} documents to the vector store.")

    document = Document.find_one({"file_id": file_id})
    await document.set({Document.metadata: rendered.metadata})
    logger.info(f"Recorded file processing in DB with file_id: {file_id}")
    return {
        "status": "success",
    }


@router.post("/add")
async def add_document(payload: PDFAddRequest):
    file_id = str(uuid4())
    orig_file_name = payload.file_name
    orig_suffix = Path(orig_file_name).suffix
    file_path = settings.DOCUMENT_DIR_PATH / f"{file_id}{orig_suffix}"
    content_bytes = base64.b64decode(payload.content)

    with open(file_path, "wb") as f:
        f.write(content_bytes)

    document = Document(
        file_id=file_id,
        file_name=orig_file_name,
        file_path=str(file_path.relative_to(settings.DOCUMENT_DIR_PATH)),
    )
    await document.insert()
    return {"status": "success"}
