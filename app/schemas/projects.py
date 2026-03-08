from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.skills import SkillPublicSchema


class ProjectImagePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    is_cover: bool
    is_video: bool
    display_order: int


class ProjectPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: Dict[str, Any]
    short_description: Dict[str, Any]
    long_description: Dict[str, Any]
    images: List[ProjectImagePublicSchema] = []

    repo_url: Optional[str]
    live_url: Optional[str]
    featured: bool = True

    skills: List[SkillPublicSchema] = []

    created_at: datetime
    updated_at: datetime


class ListProjectPublicSchema(BaseModel):
    projects: List[ProjectPublicSchema]
