from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_404_NOT_FOUND
import asyncio, logging

from app.assistant import JournalMaker
from app.crud import create_journal, get_converations_without_journal, get_conversation_history, get_multiple_journals, get_single_journal, update_journal, delete_journal
from app.database import get_db
from app.models import User
from app.oauth2 import get_current_user
from app.schemas import JournalEditData, JournalEntryData


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("journal_route")

router = APIRouter(
    prefix="/journal",
    tags=["Journal"]
)

user_dependency = Annotated[User, Depends(get_current_user)]
db_dependency = Annotated[Session, Depends(get_db)]

journal_maker = JournalMaker()


@router.get("/generate_missing")
def generate_missing_journals(user: user_dependency, db: db_dependency):
    conversation_ids = get_converations_without_journal(db, user.id)
    logger.info(f"Fetched missing conversation: {conversation_ids}")

    if not conversation_ids:
        return {"message": "All journals are up to date."}

    for conversation_id in conversation_ids:
        """Processes a single conversation and creates a journal entry."""
        chat_history = get_conversation_history(db, conversation_id, user.id)
        journal_content, mood, sentiment_score = journal_maker.summarize(chat_history)

        if journal_content:
            create_journal(db, user.id, conversation_id, journal_content, mood, sentiment_score)
            logger.info(f"Journal created for conversation {conversation_id}")
        else:
            logger.error(f"Failed to generate journal for conversation {conversation_id}")


    return {"message": "Journals are beind generated."}

@router.get("/", response_model=List[JournalEntryData])
def list_journals(limit: int, offset: int, user: user_dependency, db: db_dependency):
    return get_multiple_journals(db, user.id, limit, offset)

@router.get("/{journal_id}", response_model=JournalEntryData)
def get_journal_entry(journal_id: UUID, user: user_dependency, db: db_dependency):
    journal_entry = get_single_journal(db, user.id, journal_id)
    if not journal_entry:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Journal entry not found")

    return journal_entry 

@router.put("/{journal_id}", response_model=JournalEntryData)
def edit_journal_entry(journal_id: UUID, journal_edited_data: JournalEditData, user: user_dependency, db: db_dependency):
    content = journal_edited_data.content
    mood = journal_edited_data.mood

    journal_entry = update_journal(db, user.id, journal_id, content, mood)
    if not journal_entry:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Journal entry not found")

    return journal_entry

@router.delete("/{journal_id}")
def delete_journal_entry(journal_id: UUID, user: user_dependency, db: db_dependency):
    success = delete_journal(db, user.id, journal_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Journal entry not found")
    return {"message": "Journal entry deleted successfully"}


