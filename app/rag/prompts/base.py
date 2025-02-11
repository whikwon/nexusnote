from langchain import hub


def get_rag_prompt():
    return hub.pull("rlm/rag-prompt")
