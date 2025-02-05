from typing import List

from langchain_core.documents import Document as LangChainDocument

from .structure_manager import HierarchyLevel, HierarchyNode, StaticDocumentStructure


def create_subsection_documents(
    static_structure: StaticDocumentStructure,
) -> List[LangChainDocument]:
    """
    Traverses the static hierarchy, collects text content for each subsection and its descendants,
    and returns a list of LangChainDocument objects.
    """
    documents = []

    # Helper function to recursively collect text from a node and its children.
    def collect_text(node: HierarchyNode) -> str:
        collected_text = ""
        if node.content.text and node.content.text.content:
            collected_text += node.content.text.content + "\n\n"
        for child_id in node.children:
            child_node = static_structure.nodes.get(child_id)
            if child_node:
                collected_text += collect_text(child_node)
        return collected_text

    # Iterate over all nodes in the structure.
    for node in static_structure.nodes.values():
        if node.level == HierarchyLevel.SUBSECTION:
            # Collect content for this subsection (including all nested content).
            subsection_text = collect_text(node)
            if not subsection_text.strip():
                # Skip empty subsections.
                continue

            # Optionally, you can include subsection-specific metadata.
            metadata = {
                "id": node.id,
                "type": "subsection",
                "page_number": node.content.page_number,
                # You might include the subsection title if available:
                "title": node.content.text.content if node.content.text else "",
            }

            # Create a LangChain Document for the subsection.
            document = LangChainDocument(
                page_content=subsection_text, metadata=metadata
            )
            documents.append(document)

    return documents
