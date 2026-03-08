from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class ProfilePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    full_name: str
    headline: Dict[str, Any]
    about_text: Dict[str, Any]
    summary_text: Dict[str, Any]
    cv_spanish: Optional[str] = None
    cv_english: Optional[str] = None
    cv_portuguese: Optional[str] = None
    social_links: Dict[str, Any]
    terminal_theme: Optional[str] = None
    created_at: datetime
    updated_at: datetime
