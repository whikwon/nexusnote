from typing import Any, Dict, Generic, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from odmantic import AIOEngine
from pydantic import BaseModel

from app.core.config import settings
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def get(self, engine: AIOEngine, id: Any) -> ModelType | None:
        return await engine.find_one(self.model, self.model.id == id)

    async def get_multi(
        self, engine: AIOEngine, *, page: int = 0, page_break: bool = False
    ) -> list[ModelType]:  # noqa
        offset = (
            {"skip": page * settings.MULTI_MAX, "limit": settings.MULTI_MAX}
            if page_break
            else {}
        )  # noqa
        return await engine.find(self.model, **offset)

    async def create(self, engine: AIOEngine, *, obj_in: CreateSchemaType) -> ModelType:  # noqa
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        return await engine.save(db_obj)

    async def update(
        self,
        engine: AIOEngine,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],  # noqa
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        # TODO: Check if this saves changes with the setattr calls
        await engine.save(db_obj)
        return db_obj

    async def remove(self, engine: AIOEngine, *, id: int) -> ModelType:
        obj = await self.get(engine, id)
        if obj:
            await engine.delete(obj)
        return obj
