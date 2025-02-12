from uuid import uuid4

from beanie import Document, before_event
from beanie.odm.actions import EventTypes
from pydantic import Field

from .link import ConceptLink


class Concept(Document):
    id: str = Field(default_factory=lambda: str(uuid4()))
    comment: str

    @before_event(EventTypes.DELETE)
    async def cleanup_links(self):
        await ConceptLink.find({"concept_ids": self.id}).delete()
