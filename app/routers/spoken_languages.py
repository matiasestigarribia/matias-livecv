from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.spoken_languages import SpokenLanguage
from app.schemas.spoken_languages import SpokenLanguagePublicSchema


router = APIRouter()


@router.get(
    path='/',
    status_code=status.HTTP_200_OK,
    response_model=List[SpokenLanguagePublicSchema],
    summary='List of all spoken languages',
)
async def list_spoken_languages(
    db: AsyncSession = Depends(get_session),
):
    query = select(SpokenLanguage).order_by(SpokenLanguage.display_order)
    result = await db.execute(query)

    return result.scalars().all()
