from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class BaseModel(DeclarativeBase):
    """Base model for all database models"""
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_lower(self, value):
        if value and isinstance(value, str):
            return value.lower()
        return value

    def to_proper(self, value):
        if value and isinstance(value, str):
            return value.strip().title()
        return value

class Employee(BaseModel):
    """Employee model skeleton"""
    
    __tablename__ = "employee"
    
    employee_code = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="employee")
