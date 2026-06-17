import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import BaseModel
from .schema import AttendanceStatus

if TYPE_CHECKING:
    from app.modules.employee.model import Employee


class Attendance(BaseModel):
    """Attendance model"""
    
    __tablename__ = "attendance"
    
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employee.id"), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    check_in: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    check_out: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    total_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    undertime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    work_minutes: Mapped[int] = mapped_column(Integer, default=0)
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendances")
