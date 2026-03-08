from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SkillPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon_css_class: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ListSkillPublicSchema(BaseModel):
    skills: List[SkillPublicSchema]
