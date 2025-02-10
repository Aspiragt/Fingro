from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Message(BaseModel):
    role: str  # user o assistant
    content: str
    timestamp: datetime = datetime.now()

class Conversation(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    user_id: str
    messages: List[Message] = []
    context: Dict[str, Any] = {}  # Almacena el estado actual y variables de la conversación
    active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
