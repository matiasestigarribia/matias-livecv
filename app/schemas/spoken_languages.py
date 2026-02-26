from datetime import datetime

from typing import List, Optional, Dict

from pydantic import BaseModel, ConfigDict


class SpokenLanguagePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    language_name: Dict[str, str]
    proficiency_level: Dict[str, str]
    icon_code: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
class ListSpokenLanguageSchema(BaseModel):
    languages: List[SpokenLanguagePublicSchema]
