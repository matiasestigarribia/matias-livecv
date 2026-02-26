from datetime import datetime

from sqlalchemy import func, Boolean, String, Text 
from sqlalchemy.orm import Mapped, mapped_column

from pgvector.sqlalchemy import Vector

from app.models.base import Base


class RagDocument(Base):
    __tablename__ = 'rag_documents'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default='en')
    
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
