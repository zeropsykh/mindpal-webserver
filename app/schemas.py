from typing import List, Literal, Optional, Text
from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import date, datetime

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    dob: date
    password: str

class UserLogin(BaseModel):
    email: str | EmailStr
    password: str

class TokenData(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class ConversationData(BaseModel):
    id: UUID
    title: str
    create_time: datetime
    update_time: datetime

class MessageData(BaseModel):
    msg_id: Optional[UUID] = None
    cid: Optional[UUID] = None
    role: Literal["user", "assistant"]
    content: Text
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

class CoversationHistory(BaseModel):
    cid: UUID
    items: List[MessageData]
