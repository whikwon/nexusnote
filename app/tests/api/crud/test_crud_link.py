import pytest
from odmantic import AIOEngine

from app.crud import link as crud_link
from app.schemas.link import LinkCreate


@pytest.mark.asyncio
async def test_create_link(engine: AIOEngine) -> None:
    link_in = LinkCreate(concept_ids=["concept_id_1", "concept_id_2"])
    link = await crud_link.create(engine, obj_in=link_in)
    assert link.concept_ids == link_in.concept_ids
