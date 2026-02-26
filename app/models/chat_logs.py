from datetime import datetime

from sqlalchemy import func, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ChatLog(Base):
    __tablename__ = 'chat_logs'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_message: Mapped[str] = mapped_column(Text)
    bot_reply: Mapped[str] = mapped_column(Text)
    language: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
