from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class BaseModel(DeclarativeBase):
    """Base model for all database models"""
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_lower(self, value: Optional[str]) -> Optional[str]:
        if value:
            return value.lower()
        return value

    def to_proper(self, value: Optional[str]) -> Optional[str]:
        if value:
            return value.strip().title()
        return value

    def to_numbers(self, value: Optional[str]) -> Optional[str]:
        if value:
            return "".join(filter(str.isdigit, value))
        return value
