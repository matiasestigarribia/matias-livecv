from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.profile import Profile
from app.schemas.profile import ProfilePublicSchema

router = APIRouter()

@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=ProfilePublicSchema,
    summary='Get profile data'
)
async def get_profile(
    db: AsyncSession = Depends(get_session)
):
    profile = await db.scalar(select(Profile).limit(1))
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Profile data not found',
        )
    
    return profile
