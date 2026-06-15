from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase

class BaseModel(DeclarativeBase):
    """Base model for all database models"""
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

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
