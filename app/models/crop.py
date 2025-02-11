from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ProductionMetrics(BaseModel):
    irrigation_type: Optional[str] = None
    fertilizer_cost: Optional[float] = None
    fertilizer_frequency: Optional[str] = None
    estimated_yield: Optional[float] = None
    yield_unit: Optional[str] = None
    estimated_income: Optional[float] = None

class SalesInfo(BaseModel):
    channel: Optional[str] = None
    frequency: Optional[str] = None
    average_price: Optional[float] = None
    price_unit: Optional[str] = None

class Crop(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    type: str
    area: float
    area_unit: str  # hectáreas o cuerdas
    user_id: str
    location: Optional[dict[str, float]] = None  # lat, lng
    production: Optional[ProductionMetrics] = None
    sales: Optional[SalesInfo] = None
    notes: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
