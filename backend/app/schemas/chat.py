from datetime import datetime
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    content: str = Field(..., min_length=1, description="用户问题")


class CreateConversationRequest(BaseModel):
    title: str | None = Field(None, description="会话标题")


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    citations: list | dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
