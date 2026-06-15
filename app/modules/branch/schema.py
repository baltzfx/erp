from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class BranchBase(BaseModel):
    name: str
    description: Optional[str] = None

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class Branch(BranchBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
