import base64
from pathlib import Path
from uuid import uuid4

from odmantic import AIOEngine

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.models.concept import Concept
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    async def create(self, engine: AIOEngine, *, obj_in: DocumentCreate) -> Document:
        file_id = str(uuid4())
        orig_file_name = obj_in.name
        orig_suffix = Path(orig_file_name).suffix
        file_path = settings.DOCUMENT_DIR_PATH / f"{file_id}{orig_suffix}"
        content_bytes = base64.b64decode(obj_in.content)

        with open(file_path, "wb") as f:
            f.write(content_bytes)

        document = self.model(
            id=file_id,
            name=orig_file_name,
            path=str(file_path.relative_to(settings.DOCUMENT_DIR_PATH)),
        )
        return await super().create(engine, obj_in=document)

    async def get_with_related(
        self, engine: AIOEngine, id: str
    ) -> tuple[Document | None, list[Annotation], list[Concept]]:
        """
        Retrieves a document by its file_id along with its associated annotations and concepts.
        """
        # Retrieve the document. Note: In ODMantic the primary key is stored as _id in MongoDB.
        document = await engine.find_one(Document, {"_id": id})
        if document is None:
            return None, [], []

        # Retrieve annotations associated with this document.
        annotations = await engine.find(Annotation, {"file_id": id})

        # Extract annotation IDs.
        annotation_ids = [annotation.id for annotation in annotations]

        # Retrieve concepts linked to the annotations.
        concepts = await engine.find(
            Concept, {"annotation_ids": {"$in": annotation_ids}}
        )
        return document, annotations, concepts

    async def delete(self, engine: AIOEngine, id: str) -> Document:
        document = await super().delete(engine, id=id)

        # Remove the document file.
        document_path = settings.DOCUMENT_DIR_PATH / document.path
        document_path.unlink()

        # Find annotations associated with the document so we can later remove their references.
        annotations = await engine.find(Annotation, {"file_id": id})
        annotation_ids = [annotation.id for annotation in annotations]

        # Update each Concept that references any of the deleted annotations.
        if annotation_ids:
            # Remove all annotations for the document.
            await engine.remove(Annotation, {"file_id": id})

            # Find all concepts that contain any of the annotation_ids.
            concepts = await engine.find(
                Concept, {"annotation_ids": {"$in": annotation_ids}}
            )
            for concept in concepts:
                # Filter out the deleted annotation ids.
                concept.annotation_ids = [
                    aid for aid in concept.annotation_ids if aid not in annotation_ids
                ]
                await engine.save(concept)

        return document


document = CRUDDocument(Document)
