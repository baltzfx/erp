from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.shared.models import BaseModel

# Association table for Many-to-Many relationship between Roles and Permissions
role_permissions = Table(
    "role_permissions",
    BaseModel.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True),
)

class Permission(BaseModel):
    """Permission model"""
    
    __tablename__ = "permissions"
    
    name = Column(String(50), unique=True, index=True, nullable=False)
    codename = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
