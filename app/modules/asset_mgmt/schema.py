from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime

class AssetStatusEnum(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEPLOYED = "DEPLOYED"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE"
    DISPOSED = "DISPOSED"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    LOST = "LOST"
    STOLEN = "STOLEN"

class AssignmentStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"

class RequestStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class MaintenanceStatusEnum(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"

class AssetTypeEnum(str, Enum):
    STANDARD = "STANDARD"
    BUNDLE = "BUNDLE"
    ACCESSORY = "ACCESSORY"
    COMPONENT = "COMPONENT"
    LICENSE = "LICENSE"
    CONSUMABLE = "CONSUMABLE"
    TOOL = "TOOL"

# --- Category Schemas ---
class AssetCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class AssetCategoryCreate(AssetCategoryBase):
    pass

class AssetCategoryOut(AssetCategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Asset Schemas ---
class AssetBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    status: AssetStatusEnum = AssetStatusEnum.AVAILABLE
    asset_type: AssetTypeEnum = AssetTypeEnum.STANDARD
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    location: Optional[str] = None
    parent_asset_id: Optional[int] = None
    total_seats: Optional[int] = None
    consumed_seats: Optional[int] = 0
    salvage_value: Optional[float] = None
    useful_life_years: Optional[int] = None
    quantity: Optional[int] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[AssetStatusEnum] = None
    asset_type: Optional[AssetTypeEnum] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[float] = None
    location: Optional[str] = None
    parent_asset_id: Optional[int] = None
    total_seats: Optional[int] = None
    consumed_seats: Optional[int] = None
    salvage_value: Optional[float] = None
    useful_life_years: Optional[int] = None
    quantity: Optional[int] = None

class AssetOut(AssetBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Assignment Schemas ---
class AssetAssignmentBase(BaseModel):
    asset_id: int
    employee_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    assigned_date: date
    return_date: Optional[date] = None
    status: AssignmentStatusEnum = AssignmentStatusEnum.ACTIVE

class AssetAssignmentCreate(AssetAssignmentBase):
    pass

class AssetAssignmentOut(AssetAssignmentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Request Schemas ---
class AssetRequestBase(BaseModel):
    asset_category_id: Optional[int] = None
    asset_id: Optional[int] = None
    employee_id: int
    target_employee_id: Optional[int] = None
    target_org_unit_id: Optional[int] = None
    request_date: date
    status: RequestStatusEnum = RequestStatusEnum.PENDING
    reason: Optional[str] = None

class AssetRequestCreate(BaseModel):
    asset_category_id: Optional[int] = None
    asset_id: Optional[int] = None
    target_employee_id: Optional[int] = None
    target_org_unit_id: Optional[int] = None
    reason: Optional[str] = None

class AssetRequestOut(AssetRequestBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- Maintenance Schemas ---
class AssetMaintenanceBase(BaseModel):
    asset_id: int
    scheduled_date: date
    completion_date: Optional[date] = None
    cost: Optional[float] = None
    description: Optional[str] = None
    status: MaintenanceStatusEnum = MaintenanceStatusEnum.SCHEDULED

class AssetMaintenanceCreate(AssetMaintenanceBase):
    pass

class AssetMaintenanceOut(AssetMaintenanceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- History Schemas ---
class AssetHistoryOut(BaseModel):
    id: int
    asset_id: int
    action: str
    timestamp: datetime
    user_id: Optional[int] = None
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class BulkDeleteRequest(BaseModel):
    asset_ids: List[int]

class BulkJobOut(BaseModel):
    id: int
    job_type: str
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    error_logs: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TransferRequest(BaseModel):
    new_employee_id: Optional[int] = None
    new_org_unit_id: Optional[int] = None

class ApprovalRequest(BaseModel):
    status: RequestStatusEnum

class AssetIssueReport(BaseModel):
    description: str

class DepreciationResponse(BaseModel):
    book_value: float
    total_cost_of_ownership: float

class LicensesUpdate(BaseModel):
    consumed_seats: int
