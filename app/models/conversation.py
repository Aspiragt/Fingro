from typing import Optional, List, Dict
from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    role: str  # user o assistant
    content: str
    timestamp: datetime = datetime.now()

class Conversation(BaseModel):
    id: str
    user_id: str
    messages: List[Message] = []
    context: Dict[str, any] = {}  # Almacena el estado actual y variables de la conversación
    active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    class Config:
        from_attributes = True
