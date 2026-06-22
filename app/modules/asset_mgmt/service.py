from typing import List, Optional
import re
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

def initiate_return(db: Session, asset_id: int, user_id: Optional[int] = None):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
        
    db_asset.status = schema.AssetStatusEnum.PENDING_RETURN
    
    def _cascade_status(asset, new_status):
        for child in asset.components:
            child.status = new_status
            db.add(child)
            _cascade_status(child, new_status)
            
    _cascade_status(db_asset, schema.AssetStatusEnum.PENDING_RETURN)
    db.add(db_asset)
    db.commit()
    
    log_asset_history(db, asset_id, "Return Initiated", "Asset return process has been initiated", user_id)
    return db_asset

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
        
    # Detach from parent bundle if returned individually
    if db_asset.parent_asset_id:
        db_asset.parent_asset_id = None
        
    db_asset.status = schema.AssetStatusEnum.AVAILABLE
    
    def _cascade_status(asset, new_status):
        for child in asset.components:
            child.status = new_status
            db.add(child)
            _cascade_status(child, new_status)
            
    _cascade_status(db_asset, schema.AssetStatusEnum.AVAILABLE)
    db.add(db_asset)
    db.commit()
    
    log_asset_history(db, asset_id, "Receipt Confirmed", "Asset receipt confirmed and returned to inventory", user_id)
    return db_asset

def _asset_status_after_repair(db: Session, db_asset):
    if db_asset.parent_asset_id and db_asset.parent_asset:
        return db_asset.parent_asset.status

    assignment = db.query(model.AssetAssignment).filter(
        model.AssetAssignment.asset_id == db_asset.id,
        model.AssetAssignment.status == schema.AssignmentStatusEnum.ACTIVE
    ).first()
    if assignment:
        return schema.AssetStatusEnum.DEPLOYED

    return schema.AssetStatusEnum.AVAILABLE

def get_active_repair_request_for_asset(db: Session, asset_id: int):
    return (
        db.query(model.AssetRepairRequest)
        .filter(
            model.AssetRepairRequest.asset_id == asset_id,
            model.AssetRepairRequest.status.in_([
                schema.RepairRequestStatusEnum.REQUESTED,
                schema.RepairRequestStatusEnum.RECEIVED_BY_REPAIRMAN,
                schema.RepairRequestStatusEnum.REPAIRING,
                schema.RepairRequestStatusEnum.IN_TRANSIT,
                schema.RepairRequestStatusEnum.UNREPAIRABLE,
                schema.RepairRequestStatusEnum.SENT_BACK_TO_USER,
            ])
        )
        .order_by(model.AssetRepairRequest.id.desc())
        .first()
    )

def create_repair_request(
    db: Session,
    asset_id: int,
    requested_by_employee_id: int,
    reason: Optional[str] = None,
    user_id: Optional[int] = None
):
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return None
    if db_asset.status in [schema.AssetStatusEnum.DISPOSED, schema.AssetStatusEnum.LOST, schema.AssetStatusEnum.STOLEN]:
        return None

    existing_request = get_active_repair_request_for_asset(db, asset_id)
    if existing_request:
        return existing_request

    repair_request = model.AssetRepairRequest(
        asset_id=asset_id,
        requested_by_employee_id=requested_by_employee_id,
        request_date=date.today(),
        status=schema.RepairRequestStatusEnum.REQUESTED,
        reason=reason
    )
    db.add(repair_request)
    db.commit()
    db.refresh(repair_request)

    log_asset_history(
        db,
        asset_id,
        "Repair Requested",
        reason or "Repair request submitted",
        user_id
    )
    return repair_request

def get_repair_requests(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(model.AssetRepairRequest)
        .order_by(model.AssetRepairRequest.request_date.desc(), model.AssetRepairRequest.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_active_repair_requests_for_assets(db: Session, asset_ids: List[int]):
    if not asset_ids:
        return []
    return (
        db.query(model.AssetRepairRequest)
        .filter(
            model.AssetRepairRequest.asset_id.in_(asset_ids),
            model.AssetRepairRequest.status.in_([
                schema.RepairRequestStatusEnum.REQUESTED,
                schema.RepairRequestStatusEnum.RECEIVED_BY_REPAIRMAN,
                schema.RepairRequestStatusEnum.REPAIRING,
                schema.RepairRequestStatusEnum.IN_TRANSIT,
                schema.RepairRequestStatusEnum.UNREPAIRABLE,
                schema.RepairRequestStatusEnum.SENT_BACK_TO_USER,
            ])
        )
        .all()
    )

def get_repair_request(db: Session, request_id: int):
    return db.query(model.AssetRepairRequest).filter(model.AssetRepairRequest.id == request_id).first()

def receive_repair_request(db: Session, request_id: int, repairman_employee_id: int, user_id: Optional[int] = None):
    repair_request = get_repair_request(db, request_id)
    if not repair_request:
        return None
    if repair_request.status != schema.RepairRequestStatusEnum.REQUESTED:
        return None

    repair_request.status = schema.RepairRequestStatusEnum.RECEIVED_BY_REPAIRMAN
    repair_request.repairman_employee_id = repairman_employee_id
    repair_request.received_by_repairman_at = datetime.now()

    db_asset = get_asset(db, repair_request.asset_id)
    if db_asset:
        db_asset.status = schema.AssetStatusEnum.UNDER_MAINTENANCE
        for child in db_asset.components:
            child.status = schema.AssetStatusEnum.UNDER_MAINTENANCE
            db.add(child)
        db.add(db_asset)

    db.add(repair_request)
    db.commit()

    log_asset_history(db, repair_request.asset_id, "Repair Received", "Repairman received the asset for repair", user_id)
    return repair_request

def start_repair(db: Session, request_id: int, user_id: Optional[int] = None):
    repair_request = get_repair_request(db, request_id)
    if not repair_request:
        return None
    if repair_request.status != schema.RepairRequestStatusEnum.RECEIVED_BY_REPAIRMAN:
        return None

    repair_request.status = schema.RepairRequestStatusEnum.REPAIRING
    repair_request.repair_started_at = datetime.now()
    db.add(repair_request)
    db.commit()

    log_asset_history(db, repair_request.asset_id, "Repair Started", "Repair work started", user_id)
    return repair_request

def send_back_repair_request(db: Session, request_id: int, repair_notes: Optional[str] = None, user_id: Optional[int] = None):
    repair_request = get_repair_request(db, request_id)
    if not repair_request:
        return None
    if repair_request.status != schema.RepairRequestStatusEnum.REPAIRING:
        return None

    repair_request.status = schema.RepairRequestStatusEnum.IN_TRANSIT
    repair_request.sent_back_at = datetime.now()
    if repair_notes:
        repair_request.repair_notes = repair_notes

    db_asset = get_asset(db, repair_request.asset_id)
    if db_asset:
        db_asset.status = schema.AssetStatusEnum.IN_TRANSIT
        for child in db_asset.components:
            child.status = schema.AssetStatusEnum.IN_TRANSIT
            db.add(child)
        db.add(db_asset)

    db.add(repair_request)
    db.commit()

    log_asset_history(db, repair_request.asset_id, "Repair In Transit", repair_notes or "Repaired asset sent back to user", user_id)
    return repair_request

def confirm_repair_receipt(db: Session, request_id: int, user_id: Optional[int] = None):
    repair_request = get_repair_request(db, request_id)
    if not repair_request:
        return None
    if repair_request.status not in [
        schema.RepairRequestStatusEnum.IN_TRANSIT,
        schema.RepairRequestStatusEnum.SENT_BACK_TO_USER,
    ]:
        return None

    repair_request.status = schema.RepairRequestStatusEnum.RECEIVED_BY_USER
    repair_request.received_by_user_at = datetime.now()

    db_asset = get_asset(db, repair_request.asset_id)
    if db_asset:
        final_status = _asset_status_after_repair(db, db_asset)
        db_asset.status = final_status
        for child in db_asset.components:
            child.status = final_status
            db.add(child)
        db.add(db_asset)

    db.add(repair_request)
    db.commit()

    log_asset_history(db, repair_request.asset_id, "Repair Completed", "User received the repaired asset", user_id)
    return repair_request

def mark_unrepairable(db: Session, request_id: int, repair_notes: Optional[str] = None, user_id: Optional[int] = None):
    repair_request = get_repair_request(db, request_id)
    if not repair_request:
        return None
    if repair_request.status not in [
        schema.RepairRequestStatusEnum.RECEIVED_BY_REPAIRMAN,
        schema.RepairRequestStatusEnum.REPAIRING,
    ]:
        return None

    repair_request.status = schema.RepairRequestStatusEnum.UNREPAIRABLE
    if repair_notes:
        repair_request.repair_notes = repair_notes

    db_asset = get_asset(db, repair_request.asset_id)
    if db_asset:
        # Close out the user's accountability first, then retire the asset.
        return_asset(db, db_asset.id, user_id)
        db_asset.status = schema.AssetStatusEnum.DISPOSED
        for child in db_asset.components:
            child.status = schema.AssetStatusEnum.DISPOSED
            db.add(child)
        db.add(db_asset)

    db.add(repair_request)
    db.commit()

    log_asset_history(db, repair_request.asset_id, "Repair Unrepairable", repair_notes or "Repairman marked asset as unrepairable", user_id)
    return repair_request

def transfer_asset(db: Session, asset_id: int, new_employee_id: Optional[int] = None, new_org_unit_id: Optional[int] = None, user_id: Optional[int] = None):
    return_asset(db, asset_id, user_id)
    return assign_asset(db, asset_id, employee_id=new_employee_id, org_unit_id=new_org_unit_id, user_id=user_id)

# --- Requests ---
def get_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(model.AssetRequest).offset(skip).limit(limit).all()

def get_employee_requests(db: Session, employee_id: int):
    return db.query(model.AssetRequest).filter(model.AssetRequest.employee_id == employee_id).all()

def get_request(db: Session, request_id: int):
    return db.query(model.AssetRequest).filter(model.AssetRequest.id == request_id).first()

def get_repair_request_id_from_asset_request_reason(reason: Optional[str]) -> Optional[int]:
    if not reason:
        return None
    match = re.search(r"\[repair_request_id=(\d+)\]", reason)
    return int(match.group(1)) if match else None

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
