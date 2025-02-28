from typing import Text
from uuid import UUID
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette.types import Message

from app.assistant import JournalMaker

from .models import Conversation, JournalEntry, User, Message
from .schemas import UserRegister


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create, Update, Read, Delete

### User

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


### Conversation

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

### Journal

def create_journal(db: Session, user_id: UUID, conversation_id: UUID, content: str, mood: str, sentiment_score: float):
    journal_entry = JournalEntry(
        uid=user_id,
        cid=conversation_id,
        content=content,
        mood=mood,
        sentiment_score=sentiment_score
    )

    db.add(journal_entry)
    db.commit()
    db.refresh(journal_entry)
    return journal_entry

def get_multiple_journals(db: Session, user_id: UUID, limit: int = 5, offset: int = 0):
    journal_entries = (
        db.query(JournalEntry)
        .filter(JournalEntry.uid == user_id)
        .order_by(JournalEntry.update_time)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return journal_entries

def get_single_journal(db: Session, user_id: UUID, journal_id: UUID):
    journal_entry = db.query(JournalEntry).filter(
        JournalEntry.uid == user_id and
        JournalEntry.journal_id == journal_id
    ).first()

    return journal_entry

def update_journal(db: Session, user_id: UUID, journal_id: UUID, content: str, mood: str):
    journal_entry = get_single_journal(db, user_id, journal_id)

    if not journal_entry:
        return False

    journal_entry.content = content
    journal_entry.mood = mood

    db.commit()
    db.refresh(journal_entry)

    return journal_entry

def delete_journal(db: Session, user_id: UUID, journal_id: UUID):
    journal_entry = db.query(JournalEntry).filter(
        JournalEntry.journal_id == journal_id and 
        JournalEntry.uid == user_id
    ).first()

    if not journal_entry:
        return False

    db.delete(journal_entry)
    db.commit()
    return True

def get_converations_without_journal(db: Session, user_id: UUID):
    conversations = (
        db.query(Conversation.id)
        .outerjoin(JournalEntry, Conversation.id == JournalEntry.cid)
        .filter(Conversation.uid == user_id, JournalEntry.journal_id.is_(None))
        .all()
    )
    return [conv.id for conv in  conversations]
