from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.utils.constants import ConversationState

class Location(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.now)
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

class FinancialProfile(BaseModel):
    fingro_score: float = Field(0.0, ge=0.0, le=1000.0)
    last_calculated: datetime = Field(default_factory=datetime.now)
    factors: Dict[str, Any] = Field(default_factory=dict)
    payment_methods: List[str] = Field(default_factory=list)
    financing_history: List[Any] = Field(default_factory=list)
    references: List[Any] = Field(default_factory=list)

class ConversationState(BaseModel):
    state: ConversationState = Field(default=ConversationState.START)
    collected_data: Dict[str, Any] = Field(default_factory=dict)
    last_message_timestamp: datetime = Field(default_factory=datetime.now)
    retry_count: int = Field(default=0)

class User(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    phone_number: str
    name: Optional[str] = None
    location: Optional[Location] = None
    financial_profile: Optional[FinancialProfile] = None
    conversation_state: ConversationState = Field(default_factory=ConversationState)
    crops: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
