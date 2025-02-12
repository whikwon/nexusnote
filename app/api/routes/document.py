import base64
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request

from app.core.config import settings
from app.models import Block, Document
from app.rag.pdf_processors.marker import MarkerPDFProcessor, flatten_blocks
from app.rag.prompts.base import get_rag_prompt
from app.schemas.request import (
    DocumentProcessRequest,
    DocumentUploadRequest,
    RAGRequest,
)
from app.schemas.response import (
    ProcessDocumentResponse,
    RAGResponse,
    UploadDocumentResponse,
)
from app.schemas.section import Section, gather_section_hierarchies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/document", tags=["document"])


@router.post("/process")
async def process_document(
    request: Request, payload: DocumentProcessRequest
) -> ProcessDocumentResponse:
    app_state = request.app.state
    vector_store = app_state.vector_store
    file_id = payload.file_id

    res = await Document.find_one({"file_id": file_id})
    if res is None:
        return ProcessDocumentResponse(
            status="fail", message="File not found in DB. Please add the file first."
        )

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
        for page_number, block in enumerate(blocks)
    ]
    await Block.insert_many(blocks)

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

    return ProcessDocumentResponse(
        status="success",
        file_id=file_id,
        num_chunks=len(chunks),
    )


@router.post("/upload")
async def upload_document(payload: DocumentUploadRequest) -> UploadDocumentResponse:
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
    return UploadDocumentResponse(
        status="success",
        file_id=file_id,
        message="File uploaded successfully.",
    )


@router.post("/rag")
async def retrieve_and_respond(request: Request, payload: RAGRequest) -> RAGResponse:
    app_state = request.app.state
    vector_store = app_state.vector_store
    llm = app_state.llm

    file_id = payload.file_id
    retrieved_docs = vector_store.similarity_search(
        payload.question, k=payload.k, filter={"metadata.file_id": file_id}
    )
    logging.info(
        "Retrieved %d similar documents for the question.", len(retrieved_docs)
    )
    if len(retrieved_docs) == 0:
        return RAGResponse(
            status="fail",
            response=f"No documents found for the given file_id({file_id}).",
            question=payload.question,
        )
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    # 필요 시 기능 분리하기
    most_similar_doc = retrieved_docs[0]
    most_similar_section = await Block.find(
        {
            "file_id": file_id,
            "block_id": {"$in": most_similar_doc.metadata["block_ids"]},
        }
    ).to_list()

    prompt = get_rag_prompt()
    messages = prompt.invoke({"question": payload.question, "context": docs_content})
    response = llm.invoke(messages)
    logging.info("Generated response from the language model.")

    return RAGResponse(
        status="success",
        response=response,
        question=payload.question,
        answer=len(retrieved_docs),
        section=most_similar_section,
    )
