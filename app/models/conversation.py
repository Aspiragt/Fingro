from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.utils.constants import ConversationState

class Message(BaseModel):
    role: str  # user o assistant
    content: str
    original_content: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class ConversationContext(BaseModel):
    state: ConversationState = ConversationState.INITIAL
    collected_data: Dict[str, Any] = {}
    validation_errors: List[str] = []
    retry_count: int = 0
    last_message_timestamp: Optional[datetime] = None

class Conversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    user_id: str
    messages: List[Message] = []
    context: ConversationContext = ConversationContext()
    active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
