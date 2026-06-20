from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .model import LeaveStatus, LeaveType

class LeaveRequestBase(BaseModel):
    employee_id: int
    start_date: date
    end_date: date
    leave_type: LeaveType = LeaveType.VACATION
    reason: Optional[str] = None

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestUpdate(BaseModel):
    employee_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    leave_type: Optional[LeaveType] = None
    status: Optional[LeaveStatus] = None
    reason: Optional[str] = None

class LeaveRequestOut(LeaveRequestBase):
    id: int
    status: LeaveStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
