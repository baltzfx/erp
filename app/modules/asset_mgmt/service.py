from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date, datetime

from . import model, schema

# --- Helper: History Logging ---
def log_asset_history(db: Session, asset_id: int, action: str, details: Optional[str] = None, user_id: Optional[int] = None):
    history_entry = model.AssetHistory(
        asset_id=asset_id,
        action=action,
        timestamp=datetime.now(),
        user_id=user_id,
        details=details
    )
    db.add(history_entry)
    db.commit()

def get_asset_history(db: Session, asset_id: int):
    return db.query(model.AssetHistory).filter(model.AssetHistory.asset_id == asset_id).order_by(model.AssetHistory.timestamp.desc()).all()

# --- Asset Category ---
def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.AssetCategory).offset(skip).limit(limit).all()

def create_category(db: Session, category_in: schema.AssetCategoryCreate):
    db_cat = model.AssetCategory(**category_in.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

# --- Asset CRUD ---
def get_assets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.Asset).offset(skip).limit(limit).all()

def get_asset(db: Session, asset_id: int):
    return db.query(model.Asset).filter(model.Asset.id == asset_id).first()

def create_asset(db: Session, asset_in: schema.AssetCreate, user_id: Optional[int] = None):
    db_asset = model.Asset(**asset_in.model_dump())
    
    if db_asset.parent_asset_id:
        parent = get_asset(db, db_asset.parent_asset_id)
        if parent:
            db_asset.status = parent.status
            
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    log_asset_history(db, db_asset.id, "Created", "Asset created in the system", user_id)
    return db_asset

def update_asset(db: Session, asset_id: int, asset_in: schema.AssetUpdate, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    update_data = asset_in.model_dump(exclude_unset=True)
    changes = []
    for key, value in update_data.items():
        old_val = getattr(db_asset, key)
        if old_val != value:
            setattr(db_asset, key, value)
            changes.append(f"{key}: {old_val} -> {value}")
            
    if "parent_asset_id" in update_data and update_data["parent_asset_id"]:
        parent = get_asset(db, update_data["parent_asset_id"])
        if parent and db_asset.status != parent.status:
            changes.append(f"status: {db_asset.status.value} -> {parent.status.value}")
            db_asset.status = parent.status
            
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    if changes:
        log_asset_history(db, asset_id, "Updated", ", ".join(changes), user_id)
    return db_asset

def delete_asset(db: Session, asset_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    # Assuming soft-delete or hard delete. For now, hard delete is what is usually there.
    # But before we delete, maybe we shouldn't log history since cascade deletes history.
    db.delete(db_asset)
    db.commit()
    return db_asset

def delete_assets_bulk(db: Session, asset_ids: List[int]):
    deleted_count = 0
    for asset_id in asset_ids:
        db_asset = get_asset(db, asset_id)
        if db_asset:
            db.delete(db_asset)
            deleted_count += 1
    db.commit()
    return deleted_count

# --- Assignment & Custody ---
def get_asset_custody(db: Session, asset_id: int):
    return db.query(model.AssetAssignment).filter(model.AssetAssignment.asset_id == asset_id).order_by(model.AssetAssignment.assigned_date.desc()).all()

def assign_asset(db: Session, asset_id: int, employee_id: Optional[int] = None, org_unit_id: Optional[int] = None, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    if db_asset.asset_type == schema.AssetTypeEnum.COMPONENT or db_asset.parent_asset_id:
        raise ValueError("Cannot assign a component directly. Custody follows the parent asset.")
    
    if not employee_id and not org_unit_id:
        raise ValueError("Must provide either employee_id or org_unit_id")
        
    assignment = model.AssetAssignment(
        asset_id=asset_id,
        employee_id=employee_id,
        org_unit_id=org_unit_id,
        assigned_date=date.today()
    )
    db_asset.status = schema.AssetStatusEnum.DEPLOYED
    
    def _cascade_status(asset, new_status):
        for child in asset.components:
            child.status = new_status
            db.add(child)
            _cascade_status(child, new_status)
            
    _cascade_status(db_asset, schema.AssetStatusEnum.DEPLOYED)
    
    db.add(assignment)
    db.add(db_asset)
    db.commit()
    db.refresh(assignment)
    
    if employee_id:
        log_asset_history(db, asset_id, "Assigned", f"Assigned to employee {employee_id}", user_id)
    else:
        log_asset_history(db, asset_id, "Assigned", f"Assigned to org unit {org_unit_id}", user_id)
    return assignment

def return_asset(db: Session, asset_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
        
    assignment = db.query(model.AssetAssignment).filter(
        model.AssetAssignment.asset_id == asset_id, 
        model.AssetAssignment.status == schema.AssignmentStatusEnum.ACTIVE
    ).first()
    
    if assignment:
        assignment.status = schema.AssignmentStatusEnum.RETURNED
        assignment.return_date = date.today()
        db.add(assignment)
        
    db_asset.status = schema.AssetStatusEnum.AVAILABLE
    
    def _cascade_status(asset, new_status):
        for child in asset.components:
            child.status = new_status
            db.add(child)
            _cascade_status(child, new_status)
            
    _cascade_status(db_asset, schema.AssetStatusEnum.AVAILABLE)
    db.add(db_asset)
    db.commit()
    
    log_asset_history(db, asset_id, "Returned", "Asset returned to inventory", user_id)
    return db_asset

def transfer_asset(db: Session, asset_id: int, new_employee_id: Optional[int] = None, new_org_unit_id: Optional[int] = None, user_id: Optional[int] = None):
    return_asset(db, asset_id, user_id)
    return assign_asset(db, asset_id, employee_id=new_employee_id, org_unit_id=new_org_unit_id, user_id=user_id)

# --- Requests ---
def get_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.AssetRequest).offset(skip).limit(limit).all()

def get_employee_requests(db: Session, employee_id: int):
    return db.query(model.AssetRequest).filter(model.AssetRequest.employee_id == employee_id).all()

def create_request(db: Session, employee_id: int, request_in: schema.AssetRequestCreate):
    db_req = model.AssetRequest(
        **request_in.model_dump(),
        employee_id=employee_id,
        request_date=date.today()
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

def update_request_status(db: Session, request_id: int, status: schema.RequestStatusEnum, user_id: Optional[int] = None):
    db_req = db.query(model.AssetRequest).filter(model.AssetRequest.id == request_id).first()
    if not db_req:
        return None
    db_req.status = status
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

# --- Maintenance ---
def schedule_maintenance(db: Session, asset_id: int, maintenance_in: schema.AssetMaintenanceCreate, user_id: Optional[int] = None):
    db_main = model.AssetMaintenance(**maintenance_in.model_dump())
    db_asset = get_asset(db, asset_id)
    if db_asset:
        db_asset.status = schema.AssetStatusEnum.UNDER_MAINTENANCE
        
        def _cascade_status(asset, new_status):
            for child in asset.components:
                child.status = new_status
                db.add(child)
                _cascade_status(child, new_status)
                
        _cascade_status(db_asset, schema.AssetStatusEnum.UNDER_MAINTENANCE)
        db.add(db_asset)
    db.add(db_main)
    db.commit()
    db.refresh(db_main)
    log_asset_history(db, asset_id, "Maintenance Scheduled", maintenance_in.description, user_id)
    return db_main

def update_asset_status(db: Session, asset_id: int, status: schema.AssetStatusEnum, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    old_status = db_asset.status
    db_asset.status = status
    
    def _cascade_status(asset, new_status):
        for child in asset.components:
            child.status = new_status
            db.add(child)
            _cascade_status(child, new_status)
            
    _cascade_status(db_asset, status)
    db.add(db_asset)
    db.commit()
    
    log_asset_history(db, asset_id, "Status Changed", f"Status changed from {old_status.value} to {status.value}", user_id)
    return db_asset

# --- Bulk Jobs ---
def create_bulk_job(db: Session, job_type: str):
    db_job = model.BulkJob(job_type=job_type, status="PROCESSING")
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_bulk_job(db: Session, job_id: int):
    return db.query(model.BulkJob).filter(model.BulkJob.id == job_id).first()

# --- Asset Additional Operations ---
def calculate_depreciation(db: Session, asset_id: int):
    db_asset = get_asset(db, asset_id)
    if not db_asset or not db_asset.purchase_cost or not db_asset.useful_life_years or not db_asset.purchase_date:
        return {"book_value": 0.0, "total_cost_of_ownership": 0.0}
    
    # Calculate Straight-line depreciation
    years_used = (date.today() - db_asset.purchase_date).days / 365.25
    depreciation_per_year = float(db_asset.purchase_cost - (db_asset.salvage_value or 0)) / db_asset.useful_life_years
    book_value = max(float(db_asset.purchase_cost) - (depreciation_per_year * years_used), float(db_asset.salvage_value or 0))
    
    # Sum up maintenance costs for TCO
    maintenance_cost = sum([float(m.cost) for m in db_asset.maintenance_records if m.cost])
    tco = float(db_asset.purchase_cost) + maintenance_cost
    
    return {"book_value": round(book_value, 2), "total_cost_of_ownership": round(tco, 2)}

def report_issue(db: Session, asset_id: int, description: str, employee_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    log_asset_history(db, asset_id, "Issue Reported", description, user_id)
    
    req_in = schema.AssetRequestCreate(
        asset_id=asset_id,
        reason=f"Issue Reported: {description}"
    )
    req = model.AssetRequest(
        **req_in.model_dump(),
        employee_id=employee_id,
        request_date=date.today()
    )
    db.add(req)
    db.commit()
    return db_asset

def audit_asset(db: Session, asset_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    log_asset_history(db, asset_id, "Audited", "Physical audit checkpoint verified", user_id)
    return db_asset

def dispose_asset(db: Session, asset_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    
    db_asset.status = schema.AssetStatusEnum.DISPOSED
    db.add(db_asset)
    db.commit()
    log_asset_history(db, asset_id, "Disposed", "Asset permanently retired", user_id)
    return db_asset


# --- Licenses & Consumables ---
def update_licenses(db: Session, asset_id: int, consumed_seats: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    db_asset.consumed_seats = consumed_seats
    db.add(db_asset)
    db.commit()
    log_asset_history(db, asset_id, "Licenses Updated", f"Consumed seats updated to {consumed_seats}", user_id)
    return db_asset

def reorder_consumables(db: Session, asset_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    log_asset_history(db, asset_id, "Reorder Triggered", "Consumable stock running low, reorder initiated", user_id)
    return db_asset
