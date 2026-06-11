from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PermissionBase(BaseModel):
    name: str
    codename: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    name: Optional[str] = None
    codename: Optional[str] = None

class PermissionInDBBase(PermissionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Permission(PermissionInDBBase):
    pass
