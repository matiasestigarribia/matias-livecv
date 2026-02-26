from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.experiences import Experience
from app.schemas.experiences import ExperiencePublicSchema


router = APIRouter()

@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=List[ExperiencePublicSchema],
    summary='List of all professional experiences',
)
async def list_experiences(
    db: AsyncSession = Depends(get_session),
):
    query = select(Experience).order_by(Experience.display_order)
    result = await db.execute(query)
    
    return result.scalars().all()
