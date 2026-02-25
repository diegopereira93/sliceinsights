from typing import List, Dict
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat history")
    context: str = Field(..., description="Context string of recommended paddles")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Reply from the LLM Coach")
