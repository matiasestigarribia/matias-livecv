from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class SpokenLanguagePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    language_name: Dict[str, Any]
    proficiency_level: Dict[str, Any]
    icon_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ListSpokenLanguageSchema(BaseModel):
    languages: List[SpokenLanguagePublicSchema]
