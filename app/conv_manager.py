from cachetools import TTLCache
from threading import Lock
from uuid import UUID
from typing import Optional, Dict

from sqlalchemy.orm import Session

from .crud import create_conversation, create_message, get_conversation_history

class ConvManager:
    def __init__(self, ttl: int = 1800, max_size: int = 100):
        self.active_conversations = TTLCache(maxsize=max_size, ttl=ttl)
        self.lock = Lock()

    def start_conversation(self, user_id: UUID, db: Session):
        conversation_id = create_conversation(db, user_id).id

        state = {
            "user_id": user_id,
            "conversation_history": [],
            "question": "",
            "retrieved_docs": [],
            "generation": ""
        }

        with self.lock:
            self.active_conversations[conversation_id] = state

        return conversation_id

    def get_conversation(self, user_id: UUID, conversation_id: UUID, db: Session) -> Optional[Dict]:
        with self.lock:
            if conversation_id in self.active_conversations:
                return self.active_conversations[conversation_id]

        conversation_history = get_conversation_history(db, conversation_id, user_id)

        if conversation_history is None:
            return None

        state = {
            "user_id": user_id,
            "conversation_history": [
                {
                    "role": msg.role,
                        "content": msg.content,
                } for msg in conversation_history
            ],
            "question": "",
            "retrieved_docs": [],
            "generation": ""
        }

        with self.lock:
            self.active_conversations[conversation_id] = state

        return state

    def add_messages(self, conversation_id: UUID, role: str, content: str, db: Session):
        with self.lock:
            if conversation_id in self.active_conversations:
                self.active_conversations[conversation_id]["conversation_history"].append(
                    {
                        "role": role,
                        "content": content
                    }
                )
        create_message(db, conversation_id, role, content)

    def end_coversation(self, conversation_id: UUID):
        with self.lock:
            if conversation_id in self.active_conversations:
                del self.active_conversations[conversation_id]
