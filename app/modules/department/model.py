from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.shared.models import BaseModel
import enum

if TYPE_CHECKING:
    from app.modules.employee.model import Employee

class OrgUnitType(str, enum.Enum):
    DEPARTMENT = "DEPARTMENT"
    SECTION = "SECTION"
    TEAM = "TEAM"
    GROUP = "GROUP"

class OrgUnit(BaseModel):
    """Organizational Unit model (Polymorphic/Hierarchical)"""
    
    __tablename__ = "org_units"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_type: Mapped[OrgUnitType] = mapped_column(Enum(OrgUnitType), default=OrgUnitType.DEPARTMENT)
    
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("org_units.id"), nullable=True)
    
    parent: Mapped["OrgUnit | None"] = relationship("OrgUnit", remote_side="OrgUnit.id", back_populates="children")
    children: Mapped[list["OrgUnit"]] = relationship("OrgUnit", back_populates="parent", cascade="all, delete-orphan")
    
    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="org_unit")
