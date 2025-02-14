from odmantic import AIOEngine

from app.crud.base import CRUDBase
from app.models.link import Link
from app.schemas.common import NoUpdateSchema
from app.schemas.link import LinkCreate


class CRUDLink(CRUDBase[Link, LinkCreate, NoUpdateSchema]):
    async def update(self, engine: AIOEngine, *, db_obj: Link, obj_in: NoUpdateSchema):
        raise NotImplementedError("Update is not supported for this model")


link = CRUDLink(Link)
