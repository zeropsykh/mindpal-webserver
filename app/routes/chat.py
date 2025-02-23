from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from starlette.responses import StreamingResponse

from ..assistant import Assistant
from ..conv_manager import ConvManager

from ..schemas import ConversationData, MessageData
from ..crud import delete_conversation, get_conversation_history, get_conversations_by_user 
from ..database import get_db
from ..models import User
from ..oauth2 import get_current_user

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

user_dependency = Annotated[User, Depends(get_current_user)]
db_dependency = Annotated[Session, Depends(get_db)]

conv_manager = ConvManager()
assistant = Assistant()

@router.get("/protected")
async def protected(_: user_dependency):
    return {"message": "Hey I'am protected."}

@router.get("/start", response_description="Create chat session", response_model=ConversationData)
async def start_new_conversation(user: user_dependency, db: db_dependency):
    # chat_session = create_conversation(db, UUID(str(user.id)))
    conversation_id = conv_manager.start_conversation(UUID(str(user.id)), db)

    return conversation_id

@router.delete("/delete/{conversation_id}", response_description="Delete chat session")
async def remove_conversation(conversation_id: UUID, user: user_dependency, db: db_dependency):
    success = delete_conversation(db, conversation_id, user)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat session not found")
    return {"message": "Chat session deleted successfully"}

@router.get("/conversations", response_description="Get conversations", response_model=List[ConversationData])
async def get_conversations(limit: int, offset: int, user: user_dependency, db: db_dependency):
    return get_conversations_by_user(db, UUID(str(user.id)), limit, offset)

@router.post("/{conversation_id}/message", response_description="Stream chat response")
async def conversation(msg: MessageData, conversation_id: UUID, user: user_dependency, db: db_dependency):
    """
    Implement Server-Side Events for streaming response 
    """
    # TODO: Add message, and generated response in database

    # response_chunks = ["Hey,", "its been a long time", "since, we had a good chat,", "lets talk about what", "things happened with you"]
    # async def stream_generator():
    #     for chunk in response_chunks:
    #         if await request.is_disconnected():
    #             break
    #
    #         yield f"{chunk} "
    #         await asyncio.sleep(0.5)
    #
    # return EventSourceResponse(stream_generator())
    # return {"message": "hi"} 

    state = conv_manager.get_conversation(UUID(str(user.id)), conversation_id, db)
    if state is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    state["question"] = msg.content
    conv_manager.add_messages(conversation_id, role="user", content=msg.content, db=db)
    print(state)

    # state = assistant.workflow.invoke(state)

    async def stream_generator():
        async for response, _ in assistant.workflow.astream(
            state,
            stream_mode="messages"
        ): 
            if response.content:
                print(response.content, end="|", flush=True)
                yield f"data: {response.content}\n\n"
                state['generation'] += response.content

    conv_manager.add_messages(conversation_id, role="assistant", content=state['generation'], db=db)

    # return {"message": state["generation"]}
    return StreamingResponse(stream_generator(), media_type="text/event-stream")


@router.get("/{conversation_id}", response_description="Get conversation history")
async def conversation_history(conversation_id: UUID, user: user_dependency, db: db_dependency):
    messages = get_conversation_history(db, conversation_id, UUID(str(user.id)))

    msgs = [
        MessageData(
            msg_id=msg.msg_id,
            role=msg.role,
            content=msg.content,
            create_time=msg.create_time,
            update_time=msg.update_time
        ) for msg in messages
    ]

    return {"cid": conversation_id, "items": msgs}

@router.post("/message/{conversation_id}")
async def edit_conversation(coversation_id: str ):
    # TODO: This is for editing conversation and generating new response
    pass
