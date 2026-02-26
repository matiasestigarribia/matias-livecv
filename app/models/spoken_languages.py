from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class SpokenLanguage(Base):
    __tablename__ = 'spoken_languages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    language_name: Mapped[dict] = mapped_column(type_=JSONB)
    proficiency_level: Mapped[dict] = mapped_column(type_=JSONB)
    icon_code: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
