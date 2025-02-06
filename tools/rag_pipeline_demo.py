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
from src.pdf_helper.chunk_creator import create_root_node_documents
from src.pdf_helper.content_parser import parse_box_contents
from src.pdf_helper.document_hierarchy import TocEntry, build_document_hierarchy
from src.pdf_helper.layout_parser import LayoutExtractor
from src.pdf_helper.reference_manager import (
    ReferenceManager,
    add_title_content_references,
)
from src.utils.image import fitz_page_to_image_array


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract PDF contents for RAG pipeline demo."
    )
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


def main():
    args = parse_args()
    pdf_path = Path(args.pdf_path)
    file_name = pdf_path.name
    output_dir = Path(args.output_dir) / pdf_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize databases and models
    client = MongoClient("mongodb://localhost:27017/")
    mongo_db = client.get_database("pdf_contents")
    file_collection = mongo_db.get_collection("files")
    # New collections for static structure storage.
    node_collection = mongo_db.get_collection("document_nodes")
    relationship_collection = mongo_db.get_collection("document_relationships")
    # New collection for storing individual box contents.
    box_collection = mongo_db.get_collection("box_contents")
    lance_db_conn = lancedb.connect("db/lancedb")

    llm = OllamaLLM(model="llama3.2")
    embeddings = JinaClipV2Embeddings()
    vector_store = LanceDB(
        connection=lance_db_conn, embedding=embeddings, table_name="ai_papers"
    )

    # Check if file already processed
    res = file_collection.find_one({"file_name": file_name})
    file_id = str(uuid4()) if res is None else res["file_id"]

    if res is None:
        # Process new PDF
        doc = fitz.open(pdf_path)
        images = [fitz_page_to_image_array(page) for page in doc]

        # Extract layout
        layout_extractor = LayoutExtractor()
        layout_output = layout_extractor.extract_layout(
            images, list(range(1, len(images) + 1)), batch_size=2
        )

        # Parse contents from each page
        content_list = []
        for page_num, layout in enumerate(layout_output):
            page = doc[page_num]
            pdf_width, pdf_height = page.rect.width, page.rect.height
            img_width, img_height = layout.image_size
            w_scale = pdf_width / img_width
            h_scale = pdf_height / img_height

            for box in layout.boxes:
                content = parse_box_contents(page, box, w_scale, h_scale, file_id)
                content_list.append(content)

        # Build the static document structure.
        # Convert the PDF's table-of-contents into a list of TocEntry objects.
        toc = [
            TocEntry(level=t[0], title=t[1], page_number=t[2]) for t in doc.get_toc()
        ]
        hierarchy = build_document_hierarchy(content_list, toc)

        # Process dynamic content (e.g., create chunks for RAG)
        subsection_documents = create_root_node_documents(hierarchy)

        # Add processed documents to the vector store
        document_ids = vector_store.add_documents(subsection_documents)
        print(f"Added {len(document_ids)} documents to vector store")

        # Save the base content objects (PaddleXBoxContent) into MongoDB.
        content_dicts = [content.dict() for content in content_list]
        if content_dicts:
            box_collection.insert_many(content_dicts)
            print(f"Inserted {len(content_dicts)} box content documents")

        # Save the static document structure (GroupedNodes) into MongoDB.
        # We serialize the grouped nodes so that the "content_boxes" field contains only IDs,
        # and we recursively handle children.
        def serialize_grouped_node(node):
            data = node.dict()
            # Replace embedded PaddleXBoxContent objects with their IDs
            data["content_boxes"] = [box.id for box in node.content_boxes]
            # Recursively serialize children nodes
            data["children"] = [
                serialize_grouped_node(child) for child in node.children
            ]
            return data

        node_docs = [serialize_grouped_node(node) for node in hierarchy.root_nodes]
        if node_docs:
            node_collection.insert_many(node_docs)
            print(f"Inserted {len(node_docs)} document nodes into MongoDB")

        # Save reference relationships
        ref_manager = ReferenceManager()
        add_title_content_references(content_list, ref_manager)
        rel_docs = [rel.model_dump() for rel in ref_manager.relationships]
        if rel_docs:
            relationship_collection.insert_many(rel_docs)
            print(f"Inserted {len(rel_docs)} document relationship documents")

        # Record file processing in MongoDB
        file_collection.insert_one({"file_name": file_name, "file_id": file_id})

    # RAG Pipeline: Retrieve documents and generate a response.
    prompt = hub.pull("rlm/rag-prompt")
    retrieved_docs = vector_store.similarity_search(args.question, k=10)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    messages = prompt.invoke({"question": args.question, "context": docs_content})
    response = llm.invoke(messages)
    print("\nQuestion:", args.question)
    print("\nResponse:", response)


if __name__ == "__main__":
    main()
