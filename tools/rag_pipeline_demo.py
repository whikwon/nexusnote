# Description: Extract contents from a PDF file

import argparse
from pathlib import Path
from uuid import uuid4

import fitz
import lancedb
from langchain import hub
from langchain_community.vectorstores import LanceDB
from langchain_ollama import OllamaLLM
from pymongo import MongoClient

from src.embeddings.langchain import JinaClipV2Embeddings
from src.pdf_helper.content_extractor import chunk_layout_contents, parse_box_contents
from src.pdf_helper.content_linker import process_document_relationships
from src.pdf_helper.layout_extractor import LayoutExtractor, PaddleX17Cls
from src.utils.image import fitz_page_to_image_array
from src.utils.visualize import visualize_pdf_contents


def parse_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--pdf_path",
        type=str,
        default="assets/2501.00663v1.pdf",
        help="The path to the PDF document to process.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./outputs/extract_contents",
        help="The directory to save the output files.",
    )
    parser.add_argument(
        "--question",
        type=str,
        default="What is Titan?",
        help="The question to ask the model.",
    )
    return parser.parse_args()


def store_contents_to_mongodb(content_list, collection):
    for content in content_list:
        if not collection.find_one({"id": content.id}):
            content_dict = content.model_dump()
            content_dict["cls_id"] = content_dict["cls_id"].value
            collection.insert_one(content_dict)


def main():
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    file_name = pdf_path.name
    output_dir = Path(args.output_dir) / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    client = MongoClient("mongodb://localhost:27017/")
    mongo_db = client.get_database("pdf_contents")
    file_collection = mongo_db.get_collection("files")
    content_collection = mongo_db.get_collection("ai_papers")
    lance_db = lancedb.connect("db/lancedb")
    llm = OllamaLLM(model="llama3.2")
    embeddings = JinaClipV2Embeddings()
    vector_store = LanceDB(
        connection=lance_db, embedding=embeddings, table_name="ai_papers"
    )

    res = file_collection.find_one({"file_name": file_name})
    if res is None:
        file_id = str(uuid4())
    else:
        file_id = res["file_id"]

    if res is None:
        doc = fitz.open(pdf_path)
        images = [fitz_page_to_image_array(page) for page in doc]
        layout_extractor = LayoutExtractor()
        layout_output = layout_extractor.extract_layout(
            images, list(range(1, len(images) + 1)), batch_size=2
        )

        page = doc[0]
        content_list = []

        for page_num, res in enumerate(layout_output):
            page = doc[page_num]
            pdf_width, pdf_height = page.rect.width, page.rect.height
            img_width, img_height = res.image_size
            w_scale = pdf_width / img_width
            h_scale = pdf_height / img_height
            for box in res.boxes:
                content = parse_box_contents(page, box, w_scale, h_scale, file_id)
                content_list.append(content)

        content_list = process_document_relationships(content_list)
        store_contents_to_mongodb(content_list, content_collection)

        chunks = chunk_layout_contents(
            content_list,
            content_filter_func=lambda x: x.cls_id
            not in [
                PaddleX17Cls.number,
                PaddleX17Cls.picture,
                PaddleX17Cls.table,
                PaddleX17Cls.algorithm,
                PaddleX17Cls.formula,
            ],
            overlap_boxes=1,
        )

        visualize_pdf_contents(
            pdf_path, content_list, chunks, output_dir / "visualized_pdf.pdf"
        )

        document_ids = vector_store.add_documents(chunks)
        print("Added documents to vector store:", document_ids)

        file_collection.insert_one({"file_name": file_name, "file_id": file_id})
    else:
        print("File already exists in the database.")

    prompt = hub.pull("rlm/rag-prompt")
    retrieved_docs = vector_store.similarity_search(args.question, k=10)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    messages = prompt.invoke({"question": args.question, "context": docs_content})
    response = llm.invoke(messages)
    print("Response: ", response)


if __name__ == "__main__":
    main()
