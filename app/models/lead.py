import datetime
from typing import Optional
from pydantic import EmailStr
from sqlmodel import Field, SQLModel

class LeadBase(SQLModel):
    email: str = Field(index=True)
    name: Optional[str] = None
    converted_from: Optional[str] = Field(default="quiz_result", description="Origem da conversão")

class Lead(LeadBase, table=True):
    __tablename__ = "leads"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow,
        nullable=False,
    )
    
class LeadCreate(LeadBase):
    email: EmailStr
    
class LeadRead(LeadBase):
    id: int
    created_at: datetime.datetime
