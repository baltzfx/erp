from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.shared.models import BaseModel

class Department(BaseModel):
    """Department model"""
    
    __tablename__ = "departments"
    
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    employees = relationship("Employee", back_populates="department")
