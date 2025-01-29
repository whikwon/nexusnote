import argparse
import os
from functools import partial
from typing_extensions import List, TypedDict, Union

from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/.env"))

from langchain import hub
from langchain_core.documents import Document
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langgraph.graph import START, StateGraph


class State(TypedDict):
    question: str
    context: List[Document]
    answer: str


def retrieve(state: State, vector_store: Chroma):
    # filter: metadata filtering
    retrieved_docs = vector_store.similarity_search(
        state["question"], filter={"start_index": {"$gte": 0}}
    )
    print(retrieved_docs)
    return {"context": retrieved_docs}


def generate(state: State, llm: Union[ChatOpenAI, OllamaLLM], prompt):
    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    messages = prompt.invoke({"question": state["question"], "context": docs_content})
    response = llm.invoke(messages)
    return {"answer": response}


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
        "--question",
        type=str,
        default="What is the Titans paper about?",
        help="The question to ask the model.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.model.startswith("gpt"):
        llm = ChatOpenAI(model=args.model)
        embeddings = OpenAIEmbeddings(model=args.model)
    else:
        llm = OllamaLLM(model=args.model)
        embeddings = OllamaEmbeddings(model=args.model)

    vector_store = Chroma(
        embedding_function=embeddings,
        collection_name="ai_papers",
        persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )

    prompt = hub.pull("rlm/rag-prompt")  # RAG 관련 prompt

    retrieve_with_args = partial(retrieve, vector_store=vector_store)
    generate_with_args = partial(generate, llm=llm, prompt=prompt)

    workflow = StateGraph(State)

    # Add nodes with retry policies and configurations
    workflow.add_node("retrieve", retrieve_with_args)
    workflow.add_node("generate", generate_with_args)

    # Add edges
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")

    # Compile graph
    graph = workflow.compile()

    # Run the graph
    result = graph.invoke({"question": args.question})
    print(f'Context: {result["context"]}\n\n')
    print(f'Answer: {result["answer"]}')


if __name__ == "__main__":
    main()
