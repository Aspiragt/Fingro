from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    phone_number: str
    name: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    land_ownership: Optional[str] = None  # propio, alquilado, mixto
    payment_methods: List[str] = []  # efectivo, transferencia, etc.
    whatsapp_usage: Optional[str] = None
    phone_history: Optional[str] = None
    references: List[str] = []
    fingro_score: Optional[int] = None
    financing_history: Optional[str] = None
    financing_purpose: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    crops: List[str] = []
    active_conversation: Optional[str] = None
    referral_code: Optional[str] = None
    referral_count: int = 0
