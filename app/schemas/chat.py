from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequestSchema(BaseModel):
    message: str = Field(..., min_length=2, max_length=1500)
    language: str = Field(default='en', max_length=10)
    chat_history: Optional[List[Dict[str, str]]] = Field(default=None)


class ChatResponseSchema(BaseModel):
    reply: str
