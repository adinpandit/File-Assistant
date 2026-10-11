from fastapi import APIRouter,Depends,HTTPException,status
from app.core.auth import get_current_user
from app.models.history import ConversationResponse,ConversationListResponse,ConversationDeleteResponse,conversationCreate,MessageListResponse
from app.services.conv_store import ConversationStore
from uuid import UUID

router = APIRouter(
    prefix = "/history",
    tags = ["History"],
)

conversation_store = ConversationStore()



from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_current_user
from app.models.history import (
    ConversationResponse,
    ConversationListResponse,
    ConversationDeleteResponse,
    conversationCreate,
    MessageListResponse,
)
from app.services.conv_store import ConversationStore


router = APIRouter(
    prefix="/history",
    tags=["History"],
)


conversation_store = ConversationStore()

def validate_conversation_id(conversation_id: str) -> str:
    try:
        return str(UUID(conversation_id))

    except (ValueError, TypeError, AttributeError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID",
        ) from exc

@router.get("")
def get_history():
    return {"history":[]}

@router.post("/conversations",response_model=ConversationResponse)
def create_conversation(request:conversationCreate,current_user=Depends(get_current_user),):

    user_id = str(current_user["user_id"])

    try:
        title = request.title.strip()

        if not title:
            raise HTTPException(
                status_code=400,
                detail="Conversation title cannot be empty",
            )
        
        return conversation_store.create_conversation(
            user_id=user_id,
            title=request.title.strip(),
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation",
        ) from exc

@router.get("/conversations",response_model=ConversationListResponse,)
def list_conversations(current_user=Depends(get_current_user),):

    user_id = str(current_user["user_id"])

    try:
        conversations = conversation_store.list_conversations(user_id = user_id)

        return ConversationListResponse(conversations=conversations)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation",
        ) from exc

@router.get("/conversations/{conversation_id}",response_model = ConversationResponse,)
def get_conversation(conversation_id:str,current_user=Depends(get_current_user),):

    conversation_id = validate_conversation_id(conversation_id)
    user_id = str(current_user["user_id"])

    try:
        conversation = conversation_store.get_conversation(conversation_id = conversation_id,user_id = user_id,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation",
        ) from exc
    
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation

@router.delete("/conversations/{conversation_id}",response_model=ConversationDeleteResponse,)
def delete_conversation(conversation_id:str,current_user=Depends(get_current_user),):

    conversation_id = validate_conversation_id(conversation_id)
    user_id = str(current_user["user_id"])

    try:
        deleted = conversation_store.delete_conversation(conversation_id=conversation_id,user_id=user_id,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation",
        ) from exc
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Converstion not found",
        )

    return ConversationDeleteResponse(conversation_id=conversation_id,status="deleted",)

@router.get("/conversations/{conversation_id}/messages",response_model=MessageListResponse,)
def list_messages(conversation_id:str,current_user=Depends(get_current_user),):

    conversation_id = validate_conversation_id(conversation_id)
    user_id = str(current_user["user_id"])

    try:
        conversation = conversation_store.get_conversation(conversation_id=conversation_id,user_id=user_id,)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to verify conversation access",
        ) from exc
    
    if conversation is None:
        raise HTTPException(
            status_code = 404,
            detail = "Conversation not found",
        )

    try:
        messages = conversation_store.list_messages(conversation_id=conversation_id,user_id=user_id,)

        return MessageListResponse(messages=messages)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation messages",
        ) from exc


    