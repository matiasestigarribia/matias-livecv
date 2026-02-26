from datetime import datetime

from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


project_skills = Table(
    'project_skills',
    Base.metadata,
    Column('project_id', ForeignKey('projects.id', ondelete='CASCADE'),
           primary_key=True),
    Column('skill_id', ForeignKey('skills.id', ondelete='CASCADE'),
           primary_key=True),
)



class Project(Base):
    __tablename__ = 'projects'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str]
    title: Mapped[dict] = mapped_column(type_=JSONB)
    short_description: Mapped[dict] = mapped_column(type_=JSONB)
    long_description: Mapped[dict] = mapped_column(type_=JSONB)
    repo_url: Mapped[str | None]
    live_url: Mapped[str | None]
    featured: Mapped[bool] = mapped_column(default=True)
    images: Mapped[list['ProjectImage']] = relationship(
        back_populates='project',
        cascade='all, delete-orphan',
        lazy='selectin'
    )
    skills: Mapped[list['Skill']] = relationship(
        secondary=project_skills,
        lazy='selectin'
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __str__(self):
        if isinstance(self.title, dict):
            return self.title.get('en', self.title.get('pt', 'Untitled Project'))
        return 'Untitled Project'