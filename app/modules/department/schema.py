from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from .model import OrgUnitType

class OrgUnitBase(BaseModel):
    name: str
    description: Optional[str] = None
    unit_type: OrgUnitType = OrgUnitType.DEPARTMENT
    parent_id: Optional[int] = None

class OrgUnitCreate(OrgUnitBase):
    pass

class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    unit_type: Optional[OrgUnitType] = None
    parent_id: Optional[int] = None

class OrgUnit(OrgUnitBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Optional recursive loading
    children: List["OrgUnit"] = []

    model_config = ConfigDict(from_attributes=True)
