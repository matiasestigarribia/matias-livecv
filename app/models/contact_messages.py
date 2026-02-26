from datetime import datetime

from sqlalchemy import func, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ContactMessage(Base):
    __tablename__ = 'contact_messages'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
