from app.crud.base import CRUDBase
from app.models.annotation import Annotation
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate


class CRUDAnnotation(CRUDBase[Annotation, AnnotationCreate, AnnotationUpdate]):
    pass


annotation = CRUDAnnotation(Annotation)
