from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .model import HolidayType

class HolidayBase(BaseModel):
    name: str
    date: date
    holiday_type: HolidayType = HolidayType.REGULAR
    description: Optional[str] = None

class HolidayCreate(HolidayBase):
    pass

class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    holiday_type: Optional[HolidayType] = None
    description: Optional[str] = None

class HolidayOut(HolidayBase):
    id: int

    model_config = ConfigDict(from_attributes=True)