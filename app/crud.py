from typing import Text
from uuid import UUID
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette.types import Message

from .models import Conversation, User, Message
from .schemas import UserRegister


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create, Update, Read, Delete

def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserRegister):
    new_user = User(
        name=user.name,
        email=user.email,
        dob=user.dob,
        password=get_password_hash(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_conversation(db: Session, user_id: UUID):
    conversation = Conversation(
        uid=user_id
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation 

def delete_conversation(db: Session, conversation_id: UUID, user_id: UUID):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id and 
        Conversation.uid == user_id
    ).first()

    if not conversation:
        return False

    db.delete(conversation)
    db.commit()
    return True

def get_conversations_by_user(db: Session, user_id: UUID, limit: int = 10, offset: int = 0):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.uid == user_id)
        .order_by(Conversation.update_time)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return conversations

def create_message(db: Session, conversation_id: UUID, role: str, content: Text):
    message = Message(
        cid=conversation_id,
        role=role,
        content=content
    )

    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_conversation_history(db: Session, conversation_id: UUID, user_id: UUID):
    messages = (
        db.query(Message)
        .join(Conversation)
        .filter(Conversation.id == conversation_id)
        .order_by(Conversation.create_time)
        .all()
    )

    return messages

