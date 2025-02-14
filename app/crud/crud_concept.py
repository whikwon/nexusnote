from motor.core import AgnosticDatabase

from app.crud.base import CRUDBase
from app.models.concept import Concept
from app.models.link import Link
from app.schemas.concept import ConceptCreate, ConceptUpdate


class CRUDConcept(CRUDBase[Concept, ConceptCreate, ConceptUpdate]):
    async def create(self, db: AgnosticDatabase, *, obj_in: ConceptCreate) -> Concept:
        concept = Concept(**obj_in.model_dump())
        return await self.engine.save(concept)

    async def update(self, db: AgnosticDatabase, *, obj_in: ConceptUpdate) -> Concept:
        db_obj = await self.engine.find_one(Concept, Concept.id == obj_in.concept_id)
        if not db_obj:
            raise ValueError("Annotation not found")
        return await super().update(db, db_obj=db_obj, obj_in=obj_in)

    async def remove(self, db: AgnosticDatabase, *, id: str) -> Concept:
        # Retrieve the concept to be deleted.
        concept = await self.engine.find_one(Concept, {"_id": id})
        if concept is None:
            # Handle the case when the concept is not found.
            raise ValueError("Concept not found")

        # Cleanup: delete all Link documents that reference this concept.
        await self.engine.delete_all(Link, {"concept_ids": {"$in": [concept.id]}})

        # Now delete the concept itself.
        await self.engine.delete(concept)
        return concept


concept = CRUDConcept(Concept)
