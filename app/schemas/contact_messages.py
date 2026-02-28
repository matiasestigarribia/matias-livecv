from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class ContactMessageCreateSchema(BaseModel):
    name: str
    email: EmailStr
    message: str


class ContactMessagePublicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    message: str
    is_read: bool
    created_at: datetime
