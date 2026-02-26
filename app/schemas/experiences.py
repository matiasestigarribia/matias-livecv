from datetime import datetime, date

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ExperiencePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    company_name: str
    role: Dict[str, str]
    start_date: date
    end_date: Optional[date]
    is_current: bool
    description: Dict[str, str]
    display_order: int
    created_at: datetime
    updated_at: datetime


class ListExperiencePublicSchema(BaseModel):
    experiences: List[ExperiencePublicSchema]
