from datetime import date
from typing import Optional
from sqlalchemy import Date, String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.models import BaseModel
import enum

class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class LeaveType(str, enum.Enum):
    VACATION = "VACATION"
    SICK = "SICK"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    UNPAID = "UNPAID"

class LeaveRequest(BaseModel):
    __tablename__ = "leave_requests"

    employee_id: Mapped[int] = mapped_column(ForeignKey("employee.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    leave_type: Mapped[LeaveType] = mapped_column(Enum(LeaveType), default=LeaveType.VACATION)
    status: Mapped[LeaveStatus] = mapped_column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    employee = relationship("Employee")
