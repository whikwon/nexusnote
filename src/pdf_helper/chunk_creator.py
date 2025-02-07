from typing import List

# Adjust this import based on your LangChain version/setup.
from langchain.docstore.document import Document as LangChainDocument


def create_root_node_documents(hierarchy) -> List[LangChainDocument]:
    """
    Traverses the hierarchical document structure (represented by a DocumentHierarchy instance)
    and creates a LangChainDocument for each root GroupedNode. For each root node, the text is
    collected from all its associated content boxes and recursively from all descendant nodes.

    Args:
        hierarchy: A DocumentHierarchy instance containing the grouped node hierarchy.

    Returns:
        List[LangChainDocument]: A list of documents, each representing the content of a root node.
    """
    documents = []

    def collect_text(node) -> str:
        """Recursively collects text from a GroupedNode and its children."""
        collected_text = ""
        # Collect text from content boxes within the node.
        for box in node.content_boxes:
            # Assuming box.text is a dict with a 'content' key.
            if box.text:
                collected_text += box.text.content + "\n\n"
        # Recursively collect text from child nodes.
        for child in node.children:
            collected_text += collect_text(child)
        return collected_text

    # Process only root-level nodes.
    for node in hierarchy.root_nodes:
        node_text = collect_text(node)
        if not node_text.strip():
            # Skip nodes that yield no text.
            continue

        # Create metadata using available fields from the GroupedNode.
        metadata = {
            "id": node.id,
            "type": "root_node",
            "page_number": node.page_number,
            "title": node.title or "",
        }

        # Create a LangChain document.
        document = LangChainDocument(page_content=node_text, metadata=metadata)
        documents.append(document)

    return documents
