from enum import Enum
from typing import Optional
import datetime
from pydantic import BaseModel, ConfigDict

class AttendanceStatus(str, Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    ON_LEAVE = "On Leave"
    OFF_DUTY = "Off Duty"

class AttendanceBase(BaseModel):
    employee_id: int
    date: datetime.date
    check_in: Optional[datetime.datetime] = None
    check_out: Optional[datetime.datetime] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    total_minutes: Optional[int] = None
    late_minutes: int = 0
    undertime_minutes: int = 0
    overtime_minutes: int = 0
    work_minutes: int = 0
    remarks: Optional[str] = None

class AttendanceCreate(AttendanceBase):
    pass

class AttendanceUpdate(BaseModel):
    employee_id: Optional[int] = None
    date: Optional[datetime.date] = None
    check_in: Optional[datetime.datetime] = None
    check_out: Optional[datetime.datetime] = None
    status: Optional[AttendanceStatus] = None
    total_minutes: Optional[int] = None
    late_minutes: Optional[int] = None
    undertime_minutes: Optional[int] = None
    overtime_minutes: Optional[int] = None
    work_minutes: Optional[int] = None
    remarks: Optional[str] = None

class Attendance(AttendanceBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
