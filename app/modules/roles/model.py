from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.modules.permissions.model import role_permissions

from app.shared.models import BaseModel

class Role(BaseModel):
    """Role model"""
    
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    users = relationship("User", back_populates="role")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
