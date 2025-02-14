import base64
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from motor.core import AgnosticDatabase

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.models.concept import Concept
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    async def create(self, db: AgnosticDatabase, *, obj_in: DocumentCreate) -> Document:
        file_id = str(uuid4())
        orig_file_name = obj_in.file_name
        orig_suffix = Path(orig_file_name).suffix
        file_path = settings.DOCUMENT_DIR_PATH / f"{file_id}{orig_suffix}"
        content_bytes = base64.b64decode(obj_in.content)

        with open(file_path, "wb") as f:
            f.write(content_bytes)

        document = Document(
            id=file_id,
            name=orig_file_name,
            path=str(file_path.relative_to(settings.DOCUMENT_DIR_PATH)),
        )
        return await self.engine.save(document)

    async def get_with_related(
        self, file_id: str
    ) -> Tuple[Optional[Document], List[Annotation], List[Concept]]:
        """
        Retrieves a document by its file_id along with its associated annotations and concepts.
        """
        # Retrieve the document. Note: In ODMantic the primary key is stored as _id in MongoDB.
        document = await self.engine.find_one(Document, {"_id": file_id})
        if document is None:
            return None, [], []

        # Retrieve annotations associated with this document.
        annotations = await self.engine.find(Annotation, {"file_id": file_id}).to_list()

        # Extract annotation IDs.
        annotation_ids = [annotation.id for annotation in annotations]

        # Retrieve concepts linked to the annotations.
        concepts = await self.engine.find(
            Concept, {"annotation_ids": {"$in": annotation_ids}}
        ).to_list()
        return document, annotations, concepts


document = CRUDDocument(Document)
