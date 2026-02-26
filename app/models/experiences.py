from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Experience(Base):
    __tablename__ = 'experiences'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str]
    role: Mapped[dict] = mapped_column(type_=JSONB)
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    is_current: Mapped[bool] = mapped_column(default=False)
    description: Mapped[dict] = mapped_column(type_=JSONB)
    display_order: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
