import argparse
import os

from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.env"))

from langchain_chroma import Chroma
from langchain_community.document_loaders import PDFMinerLoader
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a simple example of a LangChain workflow."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama3.2",
        help="The model to use for the LLM and embeddings.",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        default="ai_papers",
        help="The collection name for the vector store.",
    )
    parser.add_argument(
        "--pdf_path",
        type=str,
        default="assets/2501.00663v1.pdf",
        help="The path to the PDF document to process.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    if args.model.startswith("gpt"):
        embeddings = OpenAIEmbeddings(model=args.model)
    else:
        embeddings = OllamaEmbeddings(model=args.model)
    vector_store = Chroma(
        embedding_function=embeddings,
        collection_name=args.collection_name,
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )

    # Only keep post title, headers, and content from the full HTML.
    loader = PDFMinerLoader(args.pdf_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # chunk size (characters)
        chunk_overlap=200,  # chunk overlap (characters)
        add_start_index=True,  # track index in original document
    )
    all_splits = text_splitter.split_documents(docs)
    document_ids = vector_store.add_documents(documents=all_splits)


if __name__ == "__main__":
    main()
