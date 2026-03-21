from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text
from pgvector.sqlalchemy import Vector

class AIKnowledgeBase(SQLModel, table=True):
    """Knowledge base for the AI (Influencer transcripts, guides, reviews, etc)."""
    __tablename__ = "ai_knowledge_base"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_type: str = Field(index=True)  # e.g., "youtube_video", "article", "paddle_review"
    source_url: Optional[str] = None
    title: str
    content: str = Field(sa_column=Column(Text, nullable=False))
    
    # Paddle specific relation (if this text is about a specific paddle)
    paddle_id: Optional[UUID] = Field(default=None, foreign_key="paddle_master.id")
    
    # 1536 is standard for OpenAI text-embedding-ada-002 or text-embedding-3-small
    embedding: List[float] = Field(sa_column=Column(Vector(1536)))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
