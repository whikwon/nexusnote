import argparse
import logging
import os
from pathlib import Path
from uuid import uuid4

import lancedb
from dotenv import load_dotenv
from langchain import hub
from langchain_community.vectorstores import LanceDB
from langchain_ollama import OllamaLLM
from pymongo import MongoClient

from src.embeddings.langchain import JinaClipV2Embeddings
from src.model import Block, Document, Page, Section
from src.model.section import gather_section_hierarchies
from src.pdf_processor.marker import MarkerPDFProcessor, flatten_blocks
from src.visualize import visualize_document_structure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def parse_args():
    """
    Parse command line arguments for the PDF processing pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Extract PDF contents for RAG pipeline demo."
    )
    parser.add_argument(
        "--pdf_path",
        type=str,
        default="assets/2501.00663v1.pdf",
        help="Path to the PDF document to be processed.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs/marker",
        help="Directory where output files will be saved.",
    )
    parser.add_argument(
        "--use_llm",
        action="store_true",
        help="Use the language model for processing.",
    )
    parser.add_argument(
        "--question",
        type=str,
        default="What is Titan?",
        help="Question to ask the language model.",
    )
    return parser.parse_args()


def main():
    """
    Main function to process a PDF, convert its contents, store the results,
    and run a Retrieval Augmented Generation (RAG) pipeline.
    """
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    file_name = pdf_path.name
    logging.info("Starting PDF processing for file: %s", file_name)

    client = MongoClient("mongodb://localhost:27017/")
    mongo_db = client.get_database("pdf_contents")
    document_collection = mongo_db.get_collection("documents")
    block_collection = mongo_db.get_collection("blocks")
    logging.info("Connected to MongoDB database 'pdf_contents'.")

    lance_db_conn = lancedb.connect("db/lancedb")

    llm = OllamaLLM(model="llama3.2")
    embeddings = JinaClipV2Embeddings()
    vector_store = LanceDB(
        connection=lance_db_conn, embedding=embeddings, table_name="ai_papers"
    )
    logging.info("Initialized LLM, embeddings, and vector store.")

    res = document_collection.find_one({"file_name": file_name})
    file_id = str(uuid4()) if res is None else res["file_id"]

    if res is None:
        logging.info(
            "File not found in DB. Proceeding to process new file: %s", file_name
        )

        config = {
            "output_format": "json",
        }
        if args.use_llm:
            load_dotenv(os.path.expanduser("~/.env"))
            logging.info("Loaded environment variables from ~/.env.")

            config["use_llm"] = True
            config["google_api_key"] = os.getenv("GOOGLE_API_KEY")
        logging.info("PDF conversion configuration: %s", config)

        pdf_processor = MarkerPDFProcessor(config)
        logging.info("Initialized PDF converter.")

        rendered = pdf_processor.process(pdf_path)
        blocks = flatten_blocks(rendered.children)
        blocks = [
            Block.from_JSONBlockOutput(file_id, page_number, block)
            for page_number, block in enumerate(blocks)
        ]
        block_collection.insert_many([block.model_dump() for block in blocks])

        output_dir = Path(args.output_dir) / pdf_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Created output directory: %s", output_dir)

        section_hierarchies = gather_section_hierarchies(blocks, ["1", "2"])
        sections = [
            Section.from_blocks(blocks, section_hierarchy)
            for section_hierarchy in section_hierarchies
        ]
        chunks = [section.to_chunks()[0] for section in sections]
        logging.info("Created %d chunks from the document.", len(chunks))

        document_ids = vector_store.add_documents(chunks)
        logging.info("Added %d documents to the vector store.", len(document_ids))

        document = Document.from_JSONOutput(file_id, file_name, rendered)
        document_collection.insert_one(document.model_dump())
        logging.info("Recorded file processing in MongoDB with file_id: %s", file_id)

        # TODO: visualize using blocks, sections and chunks
        visualize_document_structure(
            pdf_path, rendered, output_dir / "visualized_output.png"
        )

    prompt = hub.pull("rlm/rag-prompt")
    retrieved_docs = vector_store.similarity_search(args.question, k=10)
    logging.info(
        "Retrieved %d similar documents for the question.", len(retrieved_docs)
    )
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    messages = prompt.invoke({"question": args.question, "context": docs_content})
    response = llm.invoke(messages)
    logging.info("Generated response from the language model.")

    logging.info("Question: %s", args.question)
    logging.info("Response: %s", response)


if __name__ == "__main__":
    main()
