from enum import Enum
from typing import Dict, List, Optional, Tuple

import fitz
import networkx as nx
from pydantic import BaseModel, Field

from src.pdf_helper.content_extractor import PaddleX17Cls, PaddleXBoxContent
from src.pdf_helper.link_extractor import ContentLinker, ContentRelationship


class HierarchyLevel(str, Enum):
    DOCUMENT = "document"
    SECTION = "section"
    SUBSECTION = "subsection"
    CONTENT = "content"


class HierarchyNode(BaseModel):
    id: str
    level: HierarchyLevel
    content: PaddleXBoxContent
    parent_id: Optional[str] = None
    children: List[str] = []


class EdgeType(str, Enum):
    HIERARCHY = "hierarchy"  # Parent-child relationship
    REFERENCE = "reference"  # References between content
    TITLE = "title"  # Content-title relationships
    FOOTNOTE = "footnote"  # Content-footnote relationships
    CITATION = "citation"  # Citation relationships


class DocumentGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_index: Dict[PaddleX17Cls, List[str]] = {}

    def add_node(self, content: PaddleXBoxContent, level: HierarchyLevel) -> str:
        node_data = {
            "id": content.id,
            "level": level,
            "cls_id": content.cls_id,
            "page_number": content.page_number,
            "bbox": content.bbox,
            "file_id": content.file_id,
        }
        if content.text:
            node_data.update(
                {
                    "text_content": content.text.content,
                    "fonts": [
                        {"name": f.name, "size": f.size} for f in content.text.fonts
                    ],
                }
            )
        if content.image:
            node_data["image"] = content.image
        self.graph.add_node(content.id, **node_data)
        if content.cls_id not in self.node_index:
            self.node_index[content.cls_id] = []
        self.node_index[content.cls_id].append(content.id)
        return content.id

    def add_edge(
        self, source_id: str, target_id: str, edge_type: EdgeType, **attrs
    ) -> None:
        self.graph.add_edge(source_id, target_id, type=edge_type, **attrs)

    def _calculate_box_distance(
        self, box1: PaddleXBoxContent, box2: PaddleXBoxContent
    ) -> Tuple[float, int]:
        page_diff = abs(box1.page_number - box2.page_number)
        center1_y = (box1.bbox[1] + box1.bbox[3]) / 2
        center2_y = (box2.bbox[1] + box2.bbox[3]) / 2
        spatial_distance = abs(center2_y - center1_y)
        return spatial_distance, page_diff

    def _find_nearest_content(
        self,
        target_box: PaddleXBoxContent,
        content_type: PaddleX17Cls,
        max_boxes: int = 5,
        max_pages: int = 1,
    ) -> Optional[str]:
        """
        Find the nearest content box of specified type within given constraints.

        Args:
            target_box: The reference box to find nearest content for
            content_type: Type of content to search for (e.g., picture, table)
            max_boxes: Maximum number of boxes to check in each direction
            max_pages: Maximum page difference allowed

        Returns:
            Optional[str]: ID of the nearest content box, or None if none found
        """
        candidates = self.node_index.get(content_type, [])
        if not candidates:
            return None

        # Sort candidates by page and vertical position
        sorted_candidates = sorted(
            [(cid, self.graph.nodes[cid]) for cid in candidates],
            key=lambda x: (x[1]["page_number"], x[1]["bbox"][1]),
        )

        # Find the insertion point for target_box
        target_page = target_box.page_number
        target_y = target_box.bbox[1]

        insertion_point = 0
        for i, (_, data) in enumerate(sorted_candidates):
            if data["page_number"] > target_page or (
                data["page_number"] == target_page and data["bbox"][1] > target_y
            ):
                insertion_point = i
                break
            insertion_point = i + 1

        # Define search window
        start_idx = max(0, insertion_point - max_boxes)
        end_idx = min(len(sorted_candidates), insertion_point + max_boxes)

        # Find nearest content considering both spatial distance and page difference
        min_distance = float("inf")
        min_page_diff = float("inf")
        nearest_id = None

        for i in range(start_idx, end_idx):
            candidate_id, candidate_data = sorted_candidates[i]

            # Skip if page difference exceeds max_pages
            page_diff = abs(candidate_data["page_number"] - target_page)
            if page_diff > max_pages:
                continue

            # Create candidate box for distance calculation
            candidate_box = PaddleXBoxContent(
                id=candidate_id,
                file_id=candidate_data["file_id"],
                page_number=candidate_data["page_number"],
                bbox=candidate_data["bbox"],
                cls_id=candidate_data["cls_id"],
            )

            # Calculate distance metrics
            spatial_distance, curr_page_diff = self._calculate_box_distance(
                target_box, candidate_box
            )

            # Update nearest if this candidate is closer
            # Priority: 1. Page difference 2. Spatial distance
            if curr_page_diff < min_page_diff or (
                curr_page_diff == min_page_diff and spatial_distance < min_distance
            ):
                min_distance = spatial_distance
                min_page_diff = curr_page_diff
                nearest_id = candidate_id

        return nearest_id

    def _get_hierarchy_level(self, content: PaddleXBoxContent) -> HierarchyLevel:
        if content.cls_id != PaddleX17Cls.paragraph_title or content.text is None:
            return HierarchyLevel.CONTENT
        fonts = content.text.fonts
        max_font_size = max(font.size for font in fonts)
        if max_font_size > 16:
            return HierarchyLevel.SECTION
        elif max_font_size > 14:
            return HierarchyLevel.SUBSECTION
        else:
            return HierarchyLevel.CONTENT

    def build_graph(self, boxes: List[PaddleXBoxContent]) -> None:
        sorted_boxes = sorted(boxes, key=lambda x: (x.page_number, x.bbox[1]))
        current_section: Optional[str] = None
        current_subsection: Optional[str] = None
        for box in sorted_boxes:
            level = self._get_hierarchy_level(box)
            self.add_node(box, level)
            if level == HierarchyLevel.SECTION:
                if current_section:
                    self.add_edge(current_section, box.id, EdgeType.HIERARCHY)
                current_section = box.id
                current_subsection = None
            elif level == HierarchyLevel.SUBSECTION:
                if current_section:
                    self.add_edge(current_section, box.id, EdgeType.HIERARCHY)
                current_subsection = box.id
            else:
                parent_id = (
                    current_subsection if current_subsection else current_section
                )
                if parent_id:
                    self.add_edge(parent_id, box.id, EdgeType.HIERARCHY)

        # Link title nodes to their related content
        content_relationships = {
            PaddleX17Cls.chart_title: (PaddleX17Cls.picture, EdgeType.TITLE),
            PaddleX17Cls.table_title: (PaddleX17Cls.table, EdgeType.TITLE),
        }
        for box in sorted_boxes:
            if box.cls_id in content_relationships:
                target_type, edge_type = content_relationships[box.cls_id]
                nearest_content_id = self._find_nearest_content(box, target_type)
                if nearest_content_id:
                    candidate_data = self.graph.nodes[nearest_content_id]
                    candidate_box = PaddleXBoxContent(
                        id=nearest_content_id,
                        file_id=candidate_data["file_id"],
                        page_number=candidate_data["page_number"],
                        bbox=candidate_data["bbox"],
                        cls_id=candidate_data["cls_id"],
                    )
                    distance = self._calculate_box_distance(box, candidate_box)
                    self.add_edge(
                        box.id, nearest_content_id, edge_type, distance=distance
                    )

    def add_reference_relationships(
        self, relationships: List["ContentRelationship"]
    ) -> None:
        """
        Add reference edges (of type EdgeType.REFERENCE) to the graph.
        """
        for rel in relationships:
            self.add_edge(
                rel.source_id,
                rel.target_id,
                EdgeType.REFERENCE,
                ref_type=rel.ref_type,
                ref_text=rel.ref_text,
            )

    def build_full_graph(self, boxes: List[PaddleXBoxContent]) -> None:
        """
        Unified pipeline:
          1. Build structural graph (nodes and hierarchy/title edges).
          2. Extract reference relationships and add them as edges.
        """
        self.build_graph(boxes)

        linker = ContentLinker()
        relationships = linker.create_relationships(boxes)
        self.add_reference_relationships(relationships)

    def analyze_graph(self):
        if not self.graph.number_of_nodes():
            return {
                "num_nodes": 0,
                "num_edges": 0,
                "hierarchy_depth": 0,
                "average_degree": 0,
                "connected_components": [],
            }
        analysis = {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "connected_components": list(nx.weakly_connected_components(self.graph)),
            "average_degree": sum(dict(self.graph.degree()).values())
            / self.graph.number_of_nodes(),
            "node_types": {
                cls_id.name: len(nodes) for cls_id, nodes in self.node_index.items()
            },
            "num_components": nx.number_weakly_connected_components(self.graph),
            "largest_component_size": len(
                max(nx.weakly_connected_components(self.graph), key=len)
            ),
        }
        section_nodes = [
            n
            for n, d in self.graph.nodes(data=True)
            if d.get("level") == HierarchyLevel.SECTION
        ]
        if section_nodes:
            depths = []
            for section_node in section_nodes:
                try:
                    path_lengths = nx.single_source_shortest_path_length(
                        self.graph, section_node
                    )
                    depths.append(max(path_lengths.values()))
                except (nx.NetworkXError, ValueError):
                    continue
            analysis["hierarchy_depth"] = max(depths) if depths else 0
            analysis["num_sections"] = len(section_nodes)
        else:
            analysis["hierarchy_depth"] = 0
            analysis["num_sections"] = 0
        return analysis

    def find_path_between_nodes(self, source_id: str, target_id: str):
        try:
            path = nx.shortest_path(self.graph, source_id, target_id)
            return [self.graph.nodes[node_id] for node_id in path]
        except nx.NetworkXNoPath:
            return None

    def get_subgraph_by_type(self, node_type: PaddleX17Cls):
        nodes = self.node_index.get(node_type, [])
        return self.graph.subgraph(nodes)

    def export_to_neo4j(self, uri: str, username: str, password: str):
        try:
            import py2neo

            neo4j_graph = py2neo.Graph(uri, auth=(username, password))
            neo4j_graph.delete_all()
            neo4j_graph.run(
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:DocumentNode) REQUIRE n.id IS UNIQUE"
            )
            for node_id, data in self.graph.nodes(data=True):
                node = py2neo.Node("DocumentNode", id=node_id, **data)
                neo4j_graph.create(node)
            for source, target, data in self.graph.edges(data=True):
                source_node = neo4j_graph.nodes.match("DocumentNode", id=source).first()
                target_node = neo4j_graph.nodes.match("DocumentNode", id=target).first()
                if source_node and target_node:
                    rel = py2neo.Relationship(
                        source_node,
                        data["type"],
                        target_node,
                        **{k: v for k, v in data.items() if k != "type"},
                    )
                    neo4j_graph.create(rel)
        except ImportError:
            print(
                "Please install the py2neo package to use Neo4j export functionality."
            )
        except Exception as e:
            print(f"An error occurred while exporting to Neo4j: {e}")

    def debug_print(self):
        # Graph summary
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        print("=== Graph Summary ===")
        print(f"Nodes: {num_nodes}")
        print(f"Edges: {num_edges}")

        # Hierarchical structure with additional relationships (e.g., TITLE, REFERENCE, etc.)
        print("\n=== Hierarchical Structure with Additional Relationships ===")

        # Identify root nodes: nodes with no incoming HIERARCHY edge
        roots = []
        for node in self.graph.nodes():
            incoming_hierarchy = [
                (src, tgt, data)
                for src, tgt, data in self.graph.in_edges(node, data=True)
                if data.get("type") == EdgeType.HIERARCHY
            ]
            if not incoming_hierarchy:
                roots.append(node)

        def print_hierarchy(node_id: str, indent: int = 0, visited=None):
            if visited is None:
                visited = set()
            # Prevent infinite loops in case of cycles.
            if node_id in visited:
                print(" " * indent + f"- (Cycle detected at {node_id})")
                return
            visited.add(node_id)

            data = self.graph.nodes[node_id]
            prefix = " " * indent
            print(
                f"{prefix}- ID: {node_id}, Level: {data.get('level')}, "
                f"cls_id: {data.get('cls_id')}, page: {data.get('page_number')}"
            )

            # List any additional edges from this node (non-hierarchy)
            additional_edges = [
                (target, edge_data)
                for src, target, edge_data in self.graph.out_edges(node_id, data=True)
                if edge_data.get("type") != EdgeType.HIERARCHY
            ]
            for target, edge_data in additional_edges:
                edge_type = edge_data.get("type")
                extra_info = {k: v for k, v in edge_data.items() if k != "type"}
                print(
                    " " * (indent + 4)
                    + f"[{edge_type}] -> {target}, details: {extra_info}"
                )

            # Recursively print children from HIERARCHY edges
            children = [
                target
                for src, target, edge_data in self.graph.out_edges(node_id, data=True)
                if edge_data.get("type") == EdgeType.HIERARCHY
            ]
            for child in children:
                # Use a copy of the visited set for each branch to avoid cross-branch contamination
                print_hierarchy(child, indent + 4, visited.copy())

        if roots:
            for root in roots:
                print_hierarchy(root)
        else:
            print("No hierarchical roots found.")


class DocumentGraphVisualizer:
    def __init__(self, document_graph: "DocumentGraph"):
        self.graph = document_graph
        self.node_colors = {
            PaddleX17Cls.paragraph_title: (1, 0, 0),  # Red
            PaddleX17Cls.picture: (0, 0.7, 0),  # Green
            PaddleX17Cls.table: (0, 0, 1),  # Blue
            PaddleX17Cls.chart_title: (1, 0.5, 0),  # Orange
            PaddleX17Cls.table_title: (0.5, 0, 1),  # Purple
            PaddleX17Cls.text: (0.5, 0.5, 0.5),  # Gray
        }

    def _draw_node(self, page: fitz.Page, node_data: Dict, opacity: float = 0.3):
        """Draw a single node on the page with full node ID"""
        bbox = node_data["bbox"]
        cls_id = node_data["cls_id"]
        node_id = node_data["id"]
        color = self.node_colors.get(cls_id, (0.5, 0.5, 0.5))

        # Draw bbox rectangle
        rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
        shape = page.new_shape()
        shape.draw_rect(rect)
        shape.finish(color=color, fill=color, fill_opacity=opacity)
        shape.commit()

        # Add full node ID and type label
        label_y = bbox[1] - 8
        font_size = 6
        page.insert_text(
            (bbox[0], label_y),
            f"{node_id} ({cls_id.name})",
            fontsize=font_size,
            color=color,
        )

    def visualize(self, input_pdf_path: str, output_pdf_path: str):
        """Create a simple visual representation of document nodes"""
        doc = fitz.open(input_pdf_path)

        # Create a mapping of nodes by page
        nodes_by_page: Dict[int, List[str]] = {}
        for node_id, data in self.graph.graph.nodes(data=True):
            page_num = data["page_number"]
            if page_num not in nodes_by_page:
                nodes_by_page[page_num] = []
            nodes_by_page[page_num].append(node_id)

        # Process each page
        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc[page_idx]

            # Draw nodes for this page
            if page_num in nodes_by_page:
                for node_id in nodes_by_page[page_num]:
                    node_data = self.graph.graph.nodes[node_id]
                    self._draw_node(page, node_data)

        # Save the annotated PDF
        doc.save(output_pdf_path)
        doc.close()
