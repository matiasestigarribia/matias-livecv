from typing import List

from fastapi import APIRouter, Depends, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.projects import Project
from app.schemas.projects import ProjectPublicSchema


router = APIRouter()

@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=List[ProjectPublicSchema],
    summary='List of all projects',
)
async def list_projects(
    db: AsyncSession = Depends(get_session),
):
    
    query = select(Project).where(Project.featured == True).order_by(Project.display_order)
    result = await db.execute(query)
    
    return result.scalars().all()
