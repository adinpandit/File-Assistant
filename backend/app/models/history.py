from datetime import datetime
from pydantic import BaseModel,Field

class conversationCreate(BaseModel):
    title: str = Field(
        default="New Conversation",
        min_length = 1,
        max_length = 255,
    )

class ConversationResponse(BaseModel):
    conversation_id:str
    user_id:str
    title:str
    created_at:datetime
    updated_at:datetime

class ConversationListResponse(BaseModel):
    conversations:list[ConversationResponse]

class MessageResponse(BaseModel):
    message_id:str
    conversation_id:str
    role:str
    content:str
    created_at:datetime

class MessageListResponse(BaseModel):
    messages:list[MessageResponse]

class ConversationDeleteResponse(BaseModel):
    conversation_id:str
    status:str