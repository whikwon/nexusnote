import logging
from typing import Any

from fastapi import APIRouter, Body, Depends
from langchain_community.vectorstores import LanceDB
from odmantic import AIOEngine

from app import schemas
from app.api import deps
from app.core.config import settings
from app.crud.crud_block import block as crud_block
from app.crud.crud_document import document as crud_document
from app.rag.pdf_processors.marker import MarkerPDFProcessor, flatten_blocks
from app.rag.prompts.base import get_rag_prompt
from app.schemas.section import SectionBase, gather_section_hierarchies

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/document", tags=["document"])


@router.post(
    "/get",
    response_model=tuple[
        schemas.DocumentBase, list[schemas.AnnotationBase], list[schemas.ConceptBase]
    ],
)
async def get_document(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    id: str = Body(..., embed=True),
) -> Any:
    document, annotations, concepts = await crud_document.get_with_related(engine, id)
    return (document, annotations, concepts)


@router.post("/upload", response_model=schemas.DocumentBase)
async def upload_document(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    document_in: schemas.DocumentCreate,
) -> Any:
    document = await crud_document.create(engine, obj_in=document_in)
    return document


@router.post("/delete", response_model=schemas.Msg)
async def delete_document(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    id: str = Body(..., embed=True),
) -> Any:
    await crud_document.delete(engine, id)
    return {"msg": "File deleted successfully."}


@router.post("/process", response_model=schemas.Msg)
async def process_document(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    vector_store: LanceDB = Depends(deps.vector_store_generator),
    id: str = Body(..., embed=True),
) -> Any:
    document = await crud_document.get(engine, id)
    if document is None:
        return {"msg": "File not found in DB. Please add the file first."}

    file_path = document.path
    file_name = document.name
    pdf_path = settings.DOCUMENT_DIR_PATH / file_path
    logger.info(f"Starting PDF processing for file: {file_name}({id})")

    pdf_processor = MarkerPDFProcessor({"output_format": "json"})
    logger.info("Initialized Marker PDF processor.")

    rendered = pdf_processor.process(pdf_path)
    blocks = flatten_blocks(rendered.children)
    blocks = [
        schemas.BlockCreate.from_JSONBlockOutput(id, page_number, block)
        for page_number, block in enumerate(blocks)
    ]
    await crud_block.create_multi(engine, objs_in=blocks)

    section_hierarchies = gather_section_hierarchies(blocks, ["1", "2"])
    sections = [
        SectionBase.from_blocks(blocks, section_hierarchy)
        for section_hierarchy in section_hierarchies
    ]
    chunks = [
        section.to_chunks(embedding_model=vector_store.embeddings.name)[0]
        for section in sections
    ]
    logger.info(f"Created {len(chunks)} chunks from the document.")

    document_ids = vector_store.add_documents(chunks)
    logger.info(f"Added {len(document_ids)} documents to the vector store.")

    document_in = schemas.DocumentUpdate(metadata=rendered.metadata)
    await crud_document.update(engine, db_obj=document, obj_in=document_in)
    logger.info(f"Recorded file processing in DB with file_id: {id}")
    return {"msg": "Document processed successfully."}


@router.post("/rag", response_model=schemas.RAGResponse)
async def retrieve_and_respond(
    *,
    engine: AIOEngine = Depends(deps.engine_generator),
    vector_store: LanceDB = Depends(deps.vector_store_generator),
    llm: Any = Depends(deps.llm_generator),
    rag_request: schemas.RAGRequest,
) -> Any:
    file_id = rag_request.file_id
    retrieved_docs = vector_store.similarity_search(
        rag_request.question, k=rag_request.k, filter={"metadata.file_id": file_id}
    )
    logger.info("Retrieved %d similar documents for the question.", len(retrieved_docs))
    if len(retrieved_docs) == 0:
        return schemas.RAGResponse(
            status="fail",
            response=f"No documents found for the given file_id({file_id}).",
            question=rag_request.question,
        )
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    most_similar_doc = retrieved_docs[0]
    most_similar_section = await crud_block.get_multi(
        engine,
        {
            "file_id": file_id,
            "block_id": {"$in": most_similar_doc.metadata["block_ids"]},
        },
    )

    prompt = get_rag_prompt()
    messages = prompt.invoke(
        {"question": rag_request.question, "context": docs_content}
    )
    response = llm.invoke(messages)
    logger.info("Generated response from the language model.")

    return schemas.RAGResponse(
        status="success",
        response=response,
        question=rag_request.question,
        answer=len(retrieved_docs),
        section=most_similar_section,
    )
