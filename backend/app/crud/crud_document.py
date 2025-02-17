from odmantic import AIOEngine
from uuid import uuid4
import shutil
from pathlib import Path

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.models.concept import Concept
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    async def create(self, engine: AIOEngine, *, obj_in: DocumentCreate) -> Document:
        try:
            # Generate UUID for the file
            file_id = str(uuid4())
            
            # Create uploads directory if it doesn't exist
            upload_dir = Path(settings.DOCUMENT_DIR_PATH)
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file with UUID as filename, preserving original extension
            original_extension = Path(obj_in.name).suffix
            file_path = upload_dir / f"{file_id}{original_extension}"
            
            # Save uploaded file
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(obj_in.file.file, buffer)

            # Create document record
            db_obj = Document(
                id=file_id,  # Use the same UUID as document ID
                name=obj_in.name,
                path=str(file_path.relative_to(settings.DOCUMENT_DIR_PATH)),
                content_type=obj_in.content_type,
                metadata=obj_in.metadata or {}
            )
            await engine.save(db_obj)
            return db_obj
            
        except Exception as e:
            # Clean up file if saved but database operation failed
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            raise e

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
