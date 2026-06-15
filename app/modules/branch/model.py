from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.shared.models import BaseModel

class Branch(BaseModel):
    """Branch model"""
    
    __tablename__ = "branches"
    
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    employees = relationship("Employee", back_populates="branch")
