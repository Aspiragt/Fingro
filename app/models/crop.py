from typing import Optional, Dict
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class Crop(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: str
    name: str
    type: str
    area: float
    area_unit: str  # hectáreas o cuerdas
    user_id: str
    location: Optional[str] = None
    ownership: Optional[str] = None  # propio, alquilado
    production_amount: Optional[float] = None
    production_unit: Optional[str] = None  # quintales, libras, etc.
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    estimated_yield: Optional[float] = None
    yield_unit: Optional[str] = None
    estimated_income: Optional[float] = None
    costs: Dict[str, float] = {}
    notes: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
