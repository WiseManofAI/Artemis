# backend/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str]
    password: str
    full_name: Optional[str]
    college: Optional[str]
    enrollment: Optional[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str]
    role: Optional[str]


class ChatIn(BaseModel):
    text: str


class ChatOut(BaseModel):
    reply: str


class RiskOut(BaseModel):
    score: int
    created_at: datetime
    acknowledged: bool
