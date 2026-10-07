from fastapi import APIRouter,Depends,HTTPException,status
from app.core.auth import get_current_user
from app.models.history import ConversationResponse,ConversationListResponse,ConversationDeleteResponse,conversationCreate,MessageListResponse
from app.services.conv_store import ConversationStore

router = APIRouter(
    prefix = "/history",
    tags = ["History"],
)

conversation_store = ConversationStore()

@router.get("")
def get_history():
    return {"history":[]}

@router.post("/conversations",response_model=ConversationResponse)
def create_conversation(request:conversationCreate,current_user=Depends(get_current_user),):
    try:
        return conversation_store.create_conversation(
            user_id=str(current_user["user_id"]),
            title=request.title.strip(),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to create conversation",
        ) from exc

@router.get("/conversations",response_model=ConversationListResponse,)
def list_conversations(current_user=Depends(get_current_user),):

    try:
        conversations = conversation_store.list_conversations(user_id = str(current_user["user_id"]))

        return ConversationListResponse(conversations=conversations)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation",
        ) from exc

@router.get("/conversations/{conversation_id}",response_model = ConversationResponse,)
def get_conversation(conversation_id:str,current_user=Depends(get_current_user),):

    conversation = conversation_store.get_conversation(conversation_id = conversation_id,user_id = str(current_user["user_id"]),)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation

@router.delete("/conversations/{conversation_id}",response_model=ConversationDeleteResponse,)
def delete_conversation(conversation_id:str,current_user=Depends(get_current_user),):

    deleted = conversation_store.delete_conversation(conversation_id=conversation_id,user_id=str(current_user["user_id"]),)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Converstion not found",
        )

    return ConversationDeleteResponse(conversation_id=conversation_id,status="deleted",)

@router.get("/conversations/{conversation_id}/messages",response_model=MessageListResponse,)
def list_messages(conversation_id:str,current_user=Depends(get_current_user),):

    conversation = conversation_store.get_conversation(conversation_id=conversation_id,user_id=str(current_user["user_id"]),)

    if conversation is None:
        raise HTTPException(
            status_code = 404,
            detail = "Conversation not found",
        )

    messages = conversation_store.list_messages(conversation_id=conversation_id,user_id=str(current_user["user_id"]),)

    return MessageListResponse(messages=messages)


    
