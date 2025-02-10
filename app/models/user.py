from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    id: str
    phone_number: str
    name: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    crops: List[str] = []
    active_conversation: Optional[str] = None
    
    class Config:
        from_attributes = True
