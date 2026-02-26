from datetime import datetime

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.skills import SkillPublicSchema

class ProjectPublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    title: Dict[str, str]
    short_description: Dict[str, str]
    long_description: Dict[str, str]
    image_filename: str
    gallery_filenames: List[str]
    
    repo_url: Optional[str]
    live_url: Optional[str]
    featured: bool = True
    
    skills: List[SkillPublicSchema] = []
    
    created_at: datetime
    updated_at: datetime

    

class ListProjectPublicSchema(BaseModel):
    projects: List[ProjectPublicSchema]
