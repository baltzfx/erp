from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.users.model import User
    from app.modules.employee.model import Employee
    from app.modules.department.model import OrgUnit

from app.shared.models import BaseModel
from .schema import AssetStatusEnum, AssignmentStatusEnum, RequestStatusEnum, MaintenanceStatusEnum, AssetTypeEnum

class AssetCategory(BaseModel):
    __tablename__ = "asset_category"
    
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="category", cascade="all, delete-orphan")




class BulkJob(BaseModel):
    __tablename__ = "bulk_job"
    
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    processed_records: Mapped[int] = mapped_column(Integer, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, default=0)
    error_logs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

class Asset(BaseModel):
    __tablename__ = "asset"
    
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("asset_category.id"), nullable=False)
    status: Mapped[AssetStatusEnum] = mapped_column(Enum(AssetStatusEnum), default=AssetStatusEnum.AVAILABLE, nullable=False)
    
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    purchase_cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # New Fields
    asset_type: Mapped[AssetTypeEnum] = mapped_column(Enum(AssetTypeEnum), default=AssetTypeEnum.STANDARD, nullable=False)
    parent_asset_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("asset.id"), nullable=True)
    total_seats: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    consumed_seats: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    salvage_value: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    useful_life_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    category: Mapped["AssetCategory"] = relationship("AssetCategory", back_populates="assets")
    parent_asset: Mapped[Optional["Asset"]] = relationship("Asset", remote_side="Asset.id", back_populates="components")
    components: Mapped[List["Asset"]] = relationship("Asset", back_populates="parent_asset", cascade="all")
    assignments: Mapped[List["AssetAssignment"]] = relationship("AssetAssignment", back_populates="asset", cascade="all, delete-orphan")
    requests: Mapped[List["AssetRequest"]] = relationship("AssetRequest", back_populates="asset")
    maintenance_records: Mapped[List["AssetMaintenance"]] = relationship("AssetMaintenance", back_populates="asset", cascade="all, delete-orphan")
    history_records: Mapped[List["AssetHistory"]] = relationship("AssetHistory", back_populates="asset", cascade="all, delete-orphan")


class AssetAssignment(BaseModel):
    __tablename__ = "asset_assignment"
    
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employee.id"), nullable=True)
    org_unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("org_units.id"), nullable=True)
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[AssignmentStatusEnum] = mapped_column(Enum(AssignmentStatusEnum), default=AssignmentStatusEnum.ACTIVE, nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="assignments")
    employee: Mapped[Optional["Employee"]] = relationship("Employee")
    org_unit: Mapped[Optional["OrgUnit"]] = relationship("OrgUnit")


class AssetRequest(BaseModel):
    __tablename__ = "asset_request"
    
    asset_category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("asset_category.id"), nullable=True)
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("asset.id"), nullable=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employee.id"), nullable=False)
    target_employee_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employee.id"), nullable=True)
    target_org_unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("org_units.id"), nullable=True)
    request_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[RequestStatusEnum] = mapped_column(Enum(RequestStatusEnum), default=RequestStatusEnum.PENDING, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    category: Mapped[Optional["AssetCategory"]] = relationship("AssetCategory")
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="requests", overlaps="requests")
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])
    target_employee: Mapped[Optional["Employee"]] = relationship("Employee", foreign_keys=[target_employee_id])
    target_org_unit: Mapped[Optional["OrgUnit"]] = relationship("OrgUnit", foreign_keys=[target_org_unit_id])


class AssetMaintenance(BaseModel):
    __tablename__ = "asset_maintenance"
    
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[MaintenanceStatusEnum] = mapped_column(Enum(MaintenanceStatusEnum), default=MaintenanceStatusEnum.SCHEDULED, nullable=False)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="maintenance_records")


class AssetHistory(BaseModel):
    __tablename__ = "asset_history"
    
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("asset.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    asset: Mapped["Asset"] = relationship("Asset", back_populates="history_records")
    user: Mapped[Optional["User"]] = relationship("User")
