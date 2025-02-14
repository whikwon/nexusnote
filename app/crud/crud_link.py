from motor.core import AgnosticDatabase

from app.crud.base import CRUDBase
from app.models.link import Link
from app.schemas.common import NoUpdateSchema
from app.schemas.link import LinkCreate


class CRUDLink(CRUDBase[Link, LinkCreate, NoUpdateSchema]):
    async def create(self, db: AgnosticDatabase, *, obj_in: LinkCreate) -> Link:
        link = Link(**obj_in.model_dump())
        return await self.engine.save(link)

    async def update(
        self, db: AgnosticDatabase, *, db_obj: Link, obj_in: NoUpdateSchema
    ):
        raise NotImplementedError("Update is not supported for this model")


link = CRUDLink(Link)
