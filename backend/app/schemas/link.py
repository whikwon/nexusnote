from pydantic import BaseModel, conlist


class LinkCreate(BaseModel):
    concept_ids: conlist(str, min_length=2, max_length=2)
