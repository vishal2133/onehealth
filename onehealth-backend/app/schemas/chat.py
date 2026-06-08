from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.base import APIModel


class ConversationResponse(APIModel):
    id: int
    patient_id: int
    patient_name: str
    category: str
    avatar: str
    last_message: str | None
    last_time: datetime | None
    unread: int


class MessageCreate(APIModel):
    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message content cannot be blank")
        return value


class MessageResponse(APIModel):
    id: int
    conversation_id: int
    sender_type: str
    sender_id: int
    content: str
    sent_at: datetime
    is_read: bool
