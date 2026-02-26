from datetime import datetime
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base



class ProjectImage(Base):
    __tablename__ = 'project_images'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='CASCADE'))
    image_url: Mapped[str]
    is_cover: Mapped[bool] = mapped_column(default=False)
    is_video: Mapped[bool] = mapped_column(default=False)
    display_order: Mapped[int] = mapped_column(default=1)
    
    project: Mapped['Project'] = relationship(back_populates='images')
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __str__(self):
        return self.image_url
