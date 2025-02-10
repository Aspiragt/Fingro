from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
import json

def datetime_to_str(dt: datetime) -> str:
    return dt.isoformat() if dt else None

class Message(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: datetime_to_str}
    )
    
    role: str  # 'user' o 'assistant'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def model_dump_json(self, **kwargs) -> str:
        """Override to ensure proper datetime serialization"""
        return json.dumps(self.model_dump(), default=datetime_to_str, **kwargs)

class Conversation(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={datetime: datetime_to_str}
    )
    
    id: str
    user_id: str
    messages: List[Message] = []
    context: Dict = {}
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def model_dump_json(self, **kwargs) -> str:
        """Override to ensure proper datetime serialization"""
        return json.dumps(self.model_dump(), default=datetime_to_str, **kwargs)
