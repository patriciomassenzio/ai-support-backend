from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TicketCreate(BaseModel):
    customer_email: EmailStr
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)


class TicketUpdate(BaseModel):
    status: str = Field(pattern="^(open|in_progress|resolved|closed)$")


class TicketOut(BaseModel):
    id: int
    customer_email: str
    subject: str
    body: str
    category: str
    priority: str
    confidence: float
    suggested_reply: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class Stats(BaseModel):
    total: int
    by_category: dict[str, int]
    by_priority: dict[str, int]
    by_status: dict[str, int]
