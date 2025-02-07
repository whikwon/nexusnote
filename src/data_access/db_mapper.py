from src.pdf_helper.content_parser import PaddleXBoxContent
from src.pdf_helper.document_hierarchy import GroupedNode


def get_grouped_nodes(file_collection, box_collection, node_collection, file_id):

    def _collect_box_ids(node, box_id_set):
        """
        Recursively collect all unique box IDs from the node and its children.
        """
        # Add the current node's box IDs to the set.
        for box_id in node.get("content_boxes", []):
            box_id_set.add(box_id)
        # Recurse for each child node.
        for child in node.get("children", []):
            _collect_box_ids(child, box_id_set)

    def _set_boxes_recursively(node, box_mapping):
        """
        Set the 'boxes' field for the current node using the pre-fetched box_mapping,
        and then recursively do the same for its children.
        """
        # Map each box ID in the node to its full document using the mapping.
        node_boxes = [
            PaddleXBoxContent(**box_mapping[box_id])
            for box_id in node.get("content_boxes", [])
            if box_id in box_mapping
        ]
        node["content_boxes"] = node_boxes

    # Process all children recursively.
    for child in node.get("children", []):
        _set_boxes_recursively(child, box_mapping)

    res = file_collection.find_one()
    if res is None:
        return []

    file_id = res["file_id"]
    nodes = list(node_collection.find({"file_id": file_id}))
    if not nodes:
        return []

    # Step 1: Collect all unique box IDs from all nodes.
    all_box_ids = set()
    for node in nodes:
        _collect_box_ids(node, all_box_ids)

    # Step 2: Retrieve all boxes in one query.
    box_docs = list(box_collection.find({"id": {"$in": list(all_box_ids)}}))
    # Build a mapping from box id to box document.
    box_mapping = {box_doc["id"]: box_doc for box_doc in box_docs}

    # Step 3: Recursively assign boxes to each node.
    for node in nodes:
        _set_boxes_recursively(node, box_mapping)

    for i in range(len(nodes)):
        nodes[i] = GroupedNode(**node)

    return nodes
