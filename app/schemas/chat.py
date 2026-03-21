from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat history")
    context: str = Field(..., description="Context string of recommended paddles")
    paddle_id: Optional[UUID] = Field(default=None, description="Optional ID of the paddle being discussed to fetch rich context")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Reply from the LLM Coach")
