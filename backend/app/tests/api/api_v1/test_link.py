import pytest
from fastapi.testclient import TestClient
from odmantic import AIOEngine

from app.core.config import settings
from app.crud import concept as crud_concept
from app.schemas.concept import ConceptCreate


@pytest.mark.asyncio
async def test_create_link(engine: AIOEngine, client: TestClient):
    concept_1 = await crud_concept.create(
        engine,
        obj_in=ConceptCreate(
            name="concept_1", comment="comment_1", annotation_ids=["annotation_id_1"]
        ),
    )
    concept_2 = await crud_concept.create(
        engine,
        obj_in=ConceptCreate(
            name="concept_2", comment="comment_2", annotation_ids=["annotation_id_2"]
        ),
    )

    res = client.post(
        f"{settings.API_V1_STR}/link/create",
        json={
            "concept_ids": [concept_1.id, concept_2.id],
        },
    )
    assert res.status_code == 200
    link = res.json()
    assert "id" in link
    assert link["concept_ids"] == [concept_1.id, concept_2.id]
