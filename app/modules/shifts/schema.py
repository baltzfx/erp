from datetime import time, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

class ShiftOut(ShiftBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)