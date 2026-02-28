from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.skills import Skill
from app.schemas.skills import SkillPublicSchema


router = APIRouter()


@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=List[SkillPublicSchema],
    summary='List of all skills',
)
async def list_skills(
    db: AsyncSession = Depends(get_session)
):

    query = select(Skill).order_by(Skill.display_order)
    result = await db.execute(query)

    return result.scalars().all()
