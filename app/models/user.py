from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import datetime

class Location(BaseModel):
    latitude: float
    longitude: float
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

class FinancialProfile(BaseModel):
    fingro_score: Optional[float] = None
    payment_methods: List[str] = []
    financing_history: List[dict] = []
    references: List[dict] = []
    whatsapp_usage: Optional[str] = None
    phone_history: Optional[str] = None

class LanguageProfile(BaseModel):
    avg_message_length: float = 0
    spelling_accuracy: float = 0
    vocabulary_size: int = 0
    digital_literacy_score: float = 0
    common_mistakes: dict[str, dict] = {}

class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    phone_number: str
    name: Optional[str] = None
    location: Optional[Location] = None
    financial_profile: Optional[FinancialProfile] = None
    language_profile: Optional[LanguageProfile] = None
    crops: List[str] = []
    active_conversation: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
