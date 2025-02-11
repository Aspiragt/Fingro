"""
Modelos de datos para usuarios y conversaciones
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.utils.constants import ConversationState

class Location(BaseModel):
    """Modelo para ubicación"""
    latitude: float
    longitude: float
    municipality: Optional[str] = None
    department: Optional[str] = None

class FinancialProfile(BaseModel):
    """Modelo para perfil financiero"""
    fingro_score: Optional[float] = None
    credit_score: Optional[float] = None
    max_credit: Optional[float] = None
    risk_level: Optional[str] = None

class User(BaseModel):
    """Modelo de usuario"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    phone_number: str
    name: Optional[str] = None
    location: Optional[Location] = None
    financial_profile: Optional[FinancialProfile] = None
    conversation_state: ConversationState = Field(default=ConversationState.INICIO)
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
