from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Profile(Base):
    __tablename__ = 'profile'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str]
    headline: Mapped[dict] = mapped_column(type_=JSONB)
    about_text: Mapped[dict] = mapped_column(type_=JSONB)
    summary_text: Mapped[dict] = mapped_column(type_=JSONB)
    cv_english: Mapped[str | None]
    cv_spanish: Mapped[str | None]
    cv_portuguese: Mapped[str | None]
    social_links: Mapped[dict] = mapped_column(type_=JSONB)
    terminal_theme: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
