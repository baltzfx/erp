from datetime import date
from typing import Optional
from sqlalchemy import Date, Enum, String
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.models import BaseModel
import enum

class HolidayType(str, enum.Enum):
    REGULAR = "REGULAR"
    SPECIAL_NON_WORKING = "SPECIAL_NON_WORKING"
    COMPANY_SPECIFIC = "COMPANY_SPECIFIC"

class Holiday(BaseModel):
    __tablename__ = "holidays"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    holiday_type: Mapped[HolidayType] = mapped_column(Enum(HolidayType), default=HolidayType.REGULAR)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)