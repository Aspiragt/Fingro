"""
Esquemas para WhatsApp
"""
from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class WhatsAppMessage(BaseModel):
    """Esquema para mensajes de WhatsApp"""
    from_number: str
    message_id: str
    timestamp: datetime
    type: str
    text: Optional[dict[str, str]] = None
    location: Optional[dict[str, float]] = None
    interactive: Optional[dict[str, Any]] = None

class WhatsAppWebhook(BaseModel):
    """Esquema para webhook de WhatsApp"""
    object: str
    entry: List[dict[str, Any]]
    metadata: dict[str, str]
    contacts: List[dict[str, str]]
