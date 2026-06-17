from datetime import time
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.shared.models import BaseModel

if TYPE_CHECKING:
    from app.modules.employee.model import Employee

class Shift(BaseModel):
    """Shift model for defining working hours"""
    
    __tablename__ = "shifts"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # Relationships
    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="shift")