from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class WhatsAppMessage(BaseModel):
    """Schema for WhatsApp message"""
    message_id: str = Field(..., alias="id")
    from_number: str = Field(..., alias="from")
    timestamp: datetime
    type: str
    text: Optional[Dict[str, str]] = None
    location: Optional[Dict[str, float]] = None
    interactive: Optional[Dict[str, Any]] = None

class WhatsAppValue(BaseModel):
    """Schema for WhatsApp webhook value"""
    messaging_product: str
    metadata: Dict[str, str]
    contacts: List[Dict[str, str]]
    messages: List[WhatsAppMessage]

class WhatsAppChange(BaseModel):
    """Schema for WhatsApp webhook change"""
    value: WhatsAppValue
    field: str

class WhatsAppEntry(BaseModel):
    """Schema for WhatsApp webhook entry"""
    id: str
    changes: List[WhatsAppChange]

class WhatsAppWebhook(BaseModel):
    """Schema for WhatsApp webhook"""
    object: str
    entry: List[WhatsAppEntry]
