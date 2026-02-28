from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class SkillPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon_css_class: str
    category: str
    created_at: datetime
    updated_at: datetime


class ListSkillPublicSchema(BaseModel):
    skills: List[SkillPublicSchema]
