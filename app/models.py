from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column("user_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    password = Column(String, nullable=False)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"""<User(id={self.id}, name={self.name}, email={self.email}, username={self.username}, dob={self.dob})>"""

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column("conversation_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    uid = Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(String, default="New chat", nullable=False)
    create_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    update_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, onupdate=datetime.now(timezone.utc))

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ChatSession(cid={self.id}, uid={self.uid}, title={self.title})>"

class Message(Base):
    __tablename__ = "messages"

    msg_id = Column("msg_id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, index=True)
    cid = Column("conversation_id", UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(Enum("user", "assistant", name="role_enum"), nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    update_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, onupdate=datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(msg_id={self.msg_id})>"
