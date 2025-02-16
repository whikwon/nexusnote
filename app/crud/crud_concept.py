from odmantic import AIOEngine

from app.crud.base import CRUDBase
from app.models.concept import Concept
from app.models.link import Link
from app.schemas.concept import ConceptCreate, ConceptUpdate


class CRUDConcept(CRUDBase[Concept, ConceptCreate, ConceptUpdate]):
    async def delete(self, engine: AIOEngine, *, id: str) -> Concept:
        concept = await super().delete(engine, id=id)

        # Cleanup: delete all Link documents that reference this concept.
        await engine.remove(Link, {"concept_ids": {"$in": [id]}})
        return concept


concept = CRUDConcept(Concept)
