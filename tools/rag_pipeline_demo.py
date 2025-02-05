import argparse
from pathlib import Path
from uuid import uuid4

import fitz
import lancedb
from langchain import hub
from langchain_community.vectorstores import LanceDB
from langchain_ollama import OllamaLLM
from pymongo import MongoClient
from pymongo.collection import Collection

from src.embeddings.langchain import JinaClipV2Embeddings
from src.pdf_helper.content_extractor import parse_box_contents
from src.pdf_helper.document_processor import (
    StaticDocumentStructure,
    create_subsection_documents,
)
from src.pdf_helper.layout_extractor import LayoutExtractor
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


def store_structure_to_mongodb(
    static_structure: StaticDocumentStructure,
    node_collection: Collection,
    relationship_collection: Collection,
) -> None:
    """
    Stores the static structure nodes and reference relationships into MongoDB.

    :param static_structure: The StaticDocumentStructure instance.
    :param node_collection: MongoDB collection for hierarchy nodes.
    :param relationship_collection: MongoDB collection for reference relationships.
    """
    # Store each node
    for node in static_structure.nodes.values():
        node_dict = node.model_dump(mode="json")
        # Convert enum value to its underlying value (if any)
        node_dict["level"] = node.level.value
        # You might want to rename or remove fields as needed before storage.
        node_collection.update_one({"id": node.id}, {"$set": node_dict}, upsert=True)

    # Store each reference relationship
    for rel in static_structure.references:
        rel_dict = rel.model_dump(mode="json")
        # Convert enum to its value
        rel_dict["rel_type"] = rel.rel_type.value
        # Create a unique identifier for the relationship, e.g., based on source, target, and type
        unique_filter = {
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "rel_type": rel_dict["rel_type"],
        }
        relationship_collection.update_one(
            unique_filter, {"$set": rel_dict}, upsert=True
        )


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

        # Build the static document structure
        static_structure = StaticDocumentStructure()
        static_structure.build_hierarchy(content_list)
        static_structure.build_references()

        # Store the static structure (nodes and relationships) to MongoDB
        store_structure_to_mongodb(
            static_structure, node_collection, relationship_collection
        )

        # Process dynamic content (e.g., add embeddings)
        subsection_documents = create_subsection_documents(static_structure)

        # Add processed documents to the vector store
        document_ids = vector_store.add_documents(subsection_documents)
        print(f"Added {len(document_ids)} documents to vector store")

        # Record file processing in MongoDB
        file_collection.insert_one({"file_name": file_name, "file_id": file_id})

    # RAG Pipeline: Retrieve documents and generate a response
    prompt = hub.pull("rlm/rag-prompt")
    retrieved_docs = vector_store.similarity_search(args.question, k=10)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    messages = prompt.invoke({"question": args.question, "context": docs_content})
    response = llm.invoke(messages)
    print("\nQuestion:", args.question)
    print("\nResponse:", response)


if __name__ == "__main__":
    main()
