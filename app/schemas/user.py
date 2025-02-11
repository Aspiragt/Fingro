from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class Location(BaseModel):
    """Schema for user location"""
    latitude: float
    longitude: float
    timestamp: datetime

class FinancialProfile(BaseModel):
    """Schema for user financial profile"""
    fingro_score: float = Field(0.0, ge=0.0, le=1000.0)
    last_calculated: datetime
    factors: dict[str, Any]

class UserData(BaseModel):
    """Schema for user data"""
    location: Optional[Location] = None
    financial_profile: Optional[FinancialProfile] = None
    conversation_state: str = "START"
    last_interaction: datetime
    preferences: dict[str, Any] = Field(default_factory=dict)

class User(BaseModel):
    """Schema for user"""
    phone_number: str
    created_at: datetime
    updated_at: datetime
    data: UserData
