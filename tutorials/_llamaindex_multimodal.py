"""
https://docs.llamaindex.ai/en/stable/examples/multi_modal/ollama_cookbook/
https://lancedb.github.io/lancedb/notebooks/LlamaIndex_example/
https://github.com/run-llama/llama_index/blob/main/docs/docs/module_guides/models/multi_modal.md
"""

import argparse
import os

from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, StorageContext
from llama_index.core.indices.multi_modal.base import MultiModalVectorStoreIndex
from llama_index.core.prompts import PromptTemplate
from llama_index.embeddings.clip import ClipEmbedding
from llama_index.multi_modal_llms.ollama import OllamaMultiModal
from llama_index.vector_stores.lancedb import LanceDBVectorStore

load_dotenv(os.path.expanduser("~/.env"))


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a simple example of a LangChain workflow."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="llama:13b",
        help="The model to use for the LLM and embeddings.",
    )
    parser.add_argument(
        "--use_query_database",
        action="store_true",
    )
    parser.add_argument(
        "--sample_dir_path",
        type=str,
        default="assets/mixed_wiki/",
        help="The path to the directory containing sample documents.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    text_store = LanceDBVectorStore(uri="db/lancedb", collection_name="text_collection")
    image_store = LanceDBVectorStore(
        uri="db/lancedb", collection_name="image_collection"
    )
    storage_context = StorageContext.from_defaults(
        vector_store=text_store, image_store=image_store
    )
    image_embed_model = ClipEmbedding()
    mm_model = OllamaMultiModal(model="llava:13b")

    # If OpenAI's text embedding model is not used, an error occurs
    if not args.use_query_database:
        index = MultiModalVectorStoreIndex.from_vector_store(
            vector_store=text_store,
            image_vector_store=image_store,
            image_embed_model=image_embed_model,
        )
    else:
        documents = SimpleDirectoryReader(args.sample_dir_path).load_data()
        index = MultiModalVectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            image_embed_model=image_embed_model,
        )

    qa_tmpl_str = (
        "Context information is below.\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Given the context information and not prior knowledge, "
        "answer the query.\n"
        "Query: {query_str}\n"
        "Answer: "
    )
    qa_tmpl = PromptTemplate(qa_tmpl_str)

    retriever_engine = index.as_retriever(similarity_top_k=3, image_similarity_top_k=3)
    retrieval_results = retriever_engine.retrieve("BMW description texts")
    print(retrieval_results)

    query_engine = index.as_query_engine(llm=mm_model, text_qa_template=qa_tmpl)
    query_str = "Tell me more about the Porsche"
    response = query_engine.query(query_str)
    print(response)


if __name__ == "__main__":
    main()
