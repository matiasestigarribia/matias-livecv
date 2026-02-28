from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.contact_messages import ContactMessage
from app.schemas.contact_messages import ContactMessageCreateSchema, ContactMessagePublicSchema

router = APIRouter()


@router.post(
    path='/',
    status_code=status.HTTP_201_CREATED,
    response_model=ContactMessagePublicSchema,
    summary='Submit a new contact message',
)
async def create_new_message(
    message: ContactMessageCreateSchema,
    db: AsyncSession = Depends(get_session),
):
    db_message = ContactMessage(**message.model_dump())
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)

    return db_message
