"""
Annotation
- id: str (UUID)
- metadata: {
    type: str (drawing | text_annotation | bbox_annotation | ...),
    file_id: str (UUID)
}

Relationship
- type: str (RELEVANT | SIMILAR | ...)
"""

import uuid
from datetime import datetime

from neo4j import GraphDatabase


class Neo4jOperations:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def empty_database(self, session):
        query = """
        MATCH (ann:Annotation)
        DETACH DELETE ann
        """
        result = session.run(query)
        return result

    def create_annotation(self, tx, id, metadata):
        query = """
        CREATE (ann:Annotation)
        SET ann = $metadata, ann.id = $id, ann.created_at = datetime()
        RETURN ann
        """
        result = tx.run(query, id=id, metadata=metadata)
        return result.single()["ann"]

    def get_annotation_by_property(self, tx, property_name, property_value):
        query = f"""
        MATCH (ann:Annotation)
        WHERE ann.{property_name} = $value
        RETURN ann
        """
        result = tx.run(query, value=property_value)
        return [record["ann"] for record in result]

    def update_annotation(self, tx, id, metadata):
        query = """
        MATCH (ann:Annotation {id: $id})
        SET ann += $metadata, ann.updated_at = datetime()
        RETURN ann
        """
        result = tx.run(query, id=id, metadata=metadata)
        return result.single()["ann"]

    def delete_annotation(self, tx, name):
        query = """
        MATCH (ann:Annotation {name: $name})
        DETACH DELETE ann
        """
        tx.run(query, name=name)

    def create_relationship(self, tx, id1, id2, rel_type, rel_metadata=None):
        rel_metadata = rel_metadata or {}
        query = (
            """
        MATCH (ann1:Annotation {id: $id1})
        MATCH (ann2:Annotation {id: $id2})
        CREATE (ann1)-[r:%s]->(ann2)
        SET r += $rel_metadata
        RETURN type(r) as type
        """
            % rel_type
        )
        result = tx.run(query, id1=id1, id2=id2, rel_metadata=rel_metadata)
        return result.single()["type"] if result.peek() else None

    def find_relationships(self, tx, id, rel_type=None):
        rel_clause = f":{rel_type}" if rel_type else ""
        query = f"""
        MATCH (ann:Annotation {{id: $id}})-[r{rel_clause}]-(related)
        RETURN type(r) as type, r as relationship, related.id as related_annotation
        """
        result = tx.run(query, id=id)
        return [
            (record["type"], record["relationship"], record["related_annotation"])
            for record in result
        ]

    def find_shortest_path(self, tx, start_id, end_id, rel_type=None):
        rel_clause = f":{rel_type}*" if rel_type else "*"
        query = f"""
        MATCH path = shortestPath(
            (start:Annotation {{id: $start_id}})-[{rel_clause}]-
            (end:Annotation {{id: $end_id}})
        )
        RETURN path
        """
        result = tx.run(query, start_id=start_id, end_id=end_id)
        return result.single()["path"] if result.peek() else None


def main():
    db = Neo4jOperations("bolt://localhost:7687", "neo4j", "nexusnote")
    file_a_uuid = str(uuid.uuid4())

    ann_a_type = "drawing"
    ann_a_uuid = str(uuid.uuid4())

    ann_b_type = "text_annotation"
    ann_b_uuid = str(uuid.uuid4())

    rel_a_b_type = "RELEVANT"
    rel_a_b_metadata = {
        "updated_at": datetime.now(),
    }

    with db.driver.session() as session:
        # Create annotations
        session.execute_write(
            db.create_annotation,
            ann_a_uuid,
            {"type": ann_a_type, "file_id": file_a_uuid},
        )
        session.execute_write(
            db.create_annotation,
            ann_b_uuid,
            {"type": ann_b_type, "file_id": file_a_uuid},
        )

        # Create relationship
        session.execute_write(
            db.create_relationship,
            ann_a_uuid,
            ann_b_uuid,
            rel_a_b_type,
            rel_a_b_metadata,
        )

        # Find by metadata's property
        ann_a = session.execute_read(
            db.get_annotation_by_property, "file_id", file_a_uuid
        )
        print(f"Annotation A: {ann_a}")

        # Update annotation
        ann_a = session.execute_write(
            db.update_annotation,
            ann_a_uuid,
            {
                "updated_at": datetime.now(),
            },
        )
        print(f"Updated Annotation A: {ann_a}")

        # Find relationships
        relationships = session.execute_read(
            db.find_relationships, ann_a_uuid, rel_a_b_type
        )
        print(f"Annotation A's relationships: {relationships}")

        # Find path
        path = session.execute_read(
            db.find_shortest_path, ann_a_uuid, ann_b_uuid, rel_a_b_type
        )
        print(f"Path exists: {path}")

        db.empty_database(session)

    db.close()


if __name__ == "__main__":
    main()
