import logging
from pathlib import Path
from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, Request

from app.models import Block, Document
from app.rag.pdf_processors.marker import MarkerPDFProcessor, flatten_blocks
from app.schemas.request import PDFProcessRequest
from app.schemas.section import Section, gather_section_hierarchies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/doc", tags=["doc"])


@router.get("/extract")
async def extract_document(request: Request, process_req: PDFProcessRequest):
    app_state = request.app.state

    vector_store = app_state.vector_store

    pdf_path = Path(process_req.pdf_path)
    file_name = pdf_path.name
    file_id = process_req.file_id
    logger.info(f"Starting PDF processing for file: {file_name}({file_id})")

    res = await Document.find_one({"file_id": file_id})
    if res is None:
        logger.info(
            f"File not found in DB. Processing new file: {file_name}({file_id})"
        )
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

        document = Document.from_JSONOutput(file_id, file_name, rendered)
        await document.insert()
        logger.info(f"Recorded file processing in DB with file_id: {file_id}")
    else:
        logger.info(
            f"File found in DB. Skipping processing for file: {file_name}({file_id})"
        )
    return {
        "status": "success",
    }
