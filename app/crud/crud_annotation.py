from odmantic import AIOEngine

from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


class CRUDAnnotation(CRUDBase[Annotation, AnnotationCreate, AnnotationUpdate]):
    async def create(
        self, engine: AIOEngine, *, obj_in: AnnotationCreate
    ) -> Annotation:
        annotation = Annotation(**obj_in.model_dump())
        return await engine.save(annotation)


annotation = CRUDAnnotation(Annotation)
