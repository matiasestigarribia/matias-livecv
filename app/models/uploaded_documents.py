from datetime import datetime
from sqlalchemy import func, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class UploadedDocument(Base):
    __tablename__ = 'uploaded_documents'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(255), default='en')
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
