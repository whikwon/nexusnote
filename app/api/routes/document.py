import logging

from fastapi import APIRouter, Depends, Request
from langchain_community.vectorstores import LanceDB
from motor.core import AgnosticDatabase

from app.api import deps
from app.core.config import settings
from app.crud.document import document as crud_document
from app.models import Block, Document
from app.rag.pdf_processors.marker import MarkerPDFProcessor, flatten_blocks
from app.rag.prompts.base import get_rag_prompt
from app.schemas.request import (
    GetDocumentRequest,
    ProcessDocumentRequest,
    RAGRequest,
    UploadDocumentRequest,
)
from app.schemas.response import (
    GetDocumentResponse,
    ProcessDocumentResponse,
    RAGResponse,
    UploadDocumentResponse,
)
from app.schemas.section import Section, gather_section_hierarchies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/document", tags=["document"])


@router.post("/get")
async def get_document(
    *, db: AgnosticDatabase = Depends(deps.get_db), payload: GetDocumentRequest
) -> GetDocumentResponse:
    # Use the CRUD layer to get the document along with its related annotations and concepts.
    doc, annotations, concepts = await crud_document.get_with_related(
        file_id=payload.file_id
    )
    return GetDocumentResponse(
        status="success", document=doc, annotations=annotations, concepts=concepts
    )


@router.post("/upload")
async def upload_document(
    *, db: AgnosticDatabase = Depends(deps.get_db), payload: UploadDocumentRequest
) -> UploadDocumentResponse:
    # Let your CRUD layer handle file saving and document creation.
    doc = await crud_document.create(db, obj_in=payload)
    return UploadDocumentResponse(
        status="success",
        file_id=doc.id,
        message="File uploaded successfully.",
    )


@router.post("/process")
async def process_document(
    request: Request,
    payload: ProcessDocumentRequest,
    db: AgnosticDatabase = Depends(deps.get_db),
) -> ProcessDocumentResponse:
    app_state = request.app.state
    vector_store: LanceDB = app_state.vector_store
    file_id = payload.file_id

    # Use the CRUD engine to retrieve the document.
    doc = await crud_document.engine.find_one(Document, {"_id": file_id})
    if doc is None:
        return ProcessDocumentResponse(
            status="fail", message="File not found in DB. Please add the file first."
        )

    file_path = doc.path
    file_name = doc.name
    pdf_path = settings.DOCUMENT_DIR_PATH / file_path
    logger.info(f"Starting PDF processing for file: {file_name}({file_id})")

    pdf_processor = MarkerPDFProcessor({"output_format": "json"})
    logger.info("Initialized Marker PDF processor.")

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
    chunks = [
        section.to_chunks(embedding_model=vector_store.embeddings.name)[0]
        for section in sections
    ]
    logger.info(f"Created {len(chunks)} chunks from the document.")

    document_ids = vector_store.add_documents(chunks)
    logger.info(f"Added {len(document_ids)} documents to the vector store.")

    # Update document metadata via the CRUD engine.
    await crud_document.engine.update(doc, {"$set": {"metadata": rendered.metadata}})
    logger.info(f"Recorded file processing in DB with file_id: {file_id}")

    return ProcessDocumentResponse(
        status="success",
        file_id=file_id,
        num_chunks=len(chunks),
    )


@router.post("/rag")
async def retrieve_and_respond(request: Request, payload: RAGRequest) -> RAGResponse:
    app_state = request.app.state
    vector_store: LanceDB = app_state.vector_store
    llm = app_state.llm

    file_id = payload.file_id
    retrieved_docs = vector_store.similarity_search(
        payload.question, k=payload.k, filter={"metadata.file_id": file_id}
    )
    logger.info("Retrieved %d similar documents for the question.", len(retrieved_docs))
    if len(retrieved_docs) == 0:
        return RAGResponse(
            status="fail",
            response=f"No documents found for the given file_id({file_id}).",
            question=payload.question,
        )
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

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
    logger.info("Generated response from the language model.")

    return RAGResponse(
        status="success",
        response=response,
        question=payload.question,
        answer=len(retrieved_docs),
        section=most_similar_section,
    )
