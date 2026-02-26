from datetime import datetime

from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class ProfilePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    full_name: str
    headline: Dict[str, str]
    about_text: Dict[str, str]
    summary_text: Dict[str, str]
    cv_spanish: str
    cv_english: str
    cv_portuguese: str
    social_links: Dict[str, str]
    terminal_theme: str
    created_at: datetime
    updated_at: datetime
