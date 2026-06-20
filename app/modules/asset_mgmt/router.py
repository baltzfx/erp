from datetime import date
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.templates import templates
from app.modules.asset_mgmt import service, schema, model
from app.modules.employee import service as employee_service
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

# ==========================================
# ASSETS
# ==========================================

@router.get("/assets", response_class=HTMLResponse)
async def list_assets(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    skip: int = 0,
    limit: int = 100
):
    assets = db.query(model.Asset).filter(model.Asset.parent_asset_id == None).offset(skip).limit(limit).all()
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/assets.html",
        context={"assets": assets, "theme": theme, "user": current_user}
    )

@router.get("/assets/create", response_class=HTMLResponse)
async def create_asset_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    categories = service.get_categories(db, limit=1000)
    all_assets = service.get_assets(db, limit=1000)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/create_asset.html",
        context={
            "categories": categories,
            "all_assets": all_assets,
            "theme": theme, 
            "user": current_user,
            "asset_statuses": schema.AssetStatusEnum,
            "asset_types": schema.AssetTypeEnum
        }
    )

@router.post("/assets/create")
async def create_asset(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    name: Annotated[str, Form(...)],
    category_id: Annotated[int, Form(...)],
    description: Annotated[Optional[str], Form()] = None,
    status: Annotated[schema.AssetStatusEnum, Form()] = schema.AssetStatusEnum.AVAILABLE,
    serial_number: Annotated[Optional[str], Form()] = None,
    purchase_date: Annotated[Optional[date], Form()] = None,
    purchase_cost: Annotated[Optional[float], Form()] = None,
    location: Annotated[Optional[str], Form()] = None,
    asset_type: Annotated[schema.AssetTypeEnum, Form()] = schema.AssetTypeEnum.STANDARD,
    parent_asset_id: Annotated[Optional[int], Form()] = None,
    total_seats: Annotated[Optional[int], Form()] = None,
    salvage_value: Annotated[Optional[float], Form()] = None,
    useful_life_years: Annotated[Optional[int], Form()] = None,
    quantity: Annotated[Optional[int], Form()] = None
):
    asset_in = schema.AssetCreate(
        name=name,
        category_id=category_id,
        description=description,
        status=status,
        asset_type=asset_type,
        serial_number=serial_number,
        purchase_date=purchase_date,
        purchase_cost=purchase_cost,
        location=location,
        parent_asset_id=parent_asset_id,
        total_seats=total_seats,
        salvage_value=salvage_value,
        useful_life_years=useful_life_years,
        quantity=quantity
    )
    service.create_asset(db, asset_in, user_id=current_user.id)
    return RedirectResponse(url="/assets", status_code=303)

@router.get("/assets/{asset_id}/view", response_class=HTMLResponse)
async def view_asset_page(
    asset_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    theme = request.cookies.get("theme", "light")
    employees = employee_service.get_employees(db, limit=1000)
    from app.modules.department.model import OrgUnit
    org_units = db.query(OrgUnit).all()
    
    depreciation = service.calculate_depreciation(db, asset_id)
    available_components = db.query(model.Asset).filter(model.Asset.asset_type.in_([schema.AssetTypeEnum.COMPONENT, schema.AssetTypeEnum.ACCESSORY]), model.Asset.parent_asset_id == None, model.Asset.status == schema.AssetStatusEnum.AVAILABLE).all()
    
    available_parents = []
    if asset.asset_type in [schema.AssetTypeEnum.COMPONENT, schema.AssetTypeEnum.ACCESSORY]:
        available_parents = db.query(model.Asset).filter(
            model.Asset.asset_type.notin_([schema.AssetTypeEnum.COMPONENT, schema.AssetTypeEnum.CONSUMABLE, schema.AssetTypeEnum.ACCESSORY]),
            model.Asset.status != schema.AssetStatusEnum.DISPOSED
        ).all()
        
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/view_asset.html",
        context={
            "asset": asset,
            "employees": employees,
            "org_units": org_units,
            "depreciation": depreciation,
            "available_components": available_components,
            "available_parents": available_parents,
            "theme": theme,
            "user": current_user
        }
    )

@router.get("/assets/{asset_id}/edit", response_class=HTMLResponse)
async def edit_asset_page(
    asset_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.get_asset(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    categories = service.get_categories(db, limit=1000)
    all_assets = service.get_assets(db, limit=1000)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/edit_asset.html",
        context={
            "asset": asset,
            "categories": categories,
            "all_assets": all_assets,
            "theme": theme, 
            "user": current_user,
            "asset_statuses": schema.AssetStatusEnum,
            "asset_types": schema.AssetTypeEnum
        }
    )

@router.post("/assets/{asset_id}/edit")
async def edit_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    name: Annotated[str, Form(...)],
    category_id: Annotated[int, Form(...)],
    description: Annotated[Optional[str], Form()] = None,
    status: Annotated[schema.AssetStatusEnum, Form()] = schema.AssetStatusEnum.AVAILABLE,
    serial_number: Annotated[Optional[str], Form()] = None,
    purchase_date: Annotated[Optional[date], Form()] = None,
    purchase_cost: Annotated[Optional[float], Form()] = None,
    location: Annotated[Optional[str], Form()] = None,
    asset_type: Annotated[schema.AssetTypeEnum, Form()] = schema.AssetTypeEnum.STANDARD,
    parent_asset_id: Annotated[Optional[int], Form()] = None,
    total_seats: Annotated[Optional[int], Form()] = None,
    salvage_value: Annotated[Optional[float], Form()] = None,
    useful_life_years: Annotated[Optional[int], Form()] = None,
    quantity: Annotated[Optional[int], Form()] = None
):
    asset_in = schema.AssetUpdate(
        name=name,
        category_id=category_id,
        description=description,
        status=status,
        asset_type=asset_type,
        serial_number=serial_number,
        purchase_date=purchase_date,
        purchase_cost=purchase_cost,
        location=location,
        parent_asset_id=parent_asset_id,
        total_seats=total_seats,
        salvage_value=salvage_value,
        useful_life_years=useful_life_years,
        quantity=quantity
    )
    service.update_asset(db, asset_id, asset_in, user_id=current_user.id)
    return RedirectResponse(url="/assets", status_code=303)

@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_asset(db, asset_id, user_id=current_user.id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)

# ==========================================
# ASSET CATEGORIES
# ==========================================

@router.get("/asset-categories", response_class=HTMLResponse)
async def list_categories(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    skip: int = 0,
    limit: int = 100
):
    categories = service.get_categories(db, skip=skip, limit=limit)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/categories.html",
        context={"categories": categories, "theme": theme, "user": current_user}
    )

@router.get("/asset-categories/create", response_class=HTMLResponse)
async def create_category_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/create_categories.html",
        context={"theme": theme, "user": current_user}
    )

@router.post("/asset-categories/create")
async def create_category(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    name: Annotated[str, Form(...)],
    description: Annotated[Optional[str], Form()] = None
):
    category_in = schema.AssetCategoryCreate(name=name, description=description)
    service.create_category(db, category_in)
    return RedirectResponse(url="/asset-categories", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/asset-categories/{category_id}/edit", response_class=HTMLResponse)
async def edit_category_page(
    category_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    category = db.query(model.AssetCategory).filter(model.AssetCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/edit_categories.html",
        context={"category": category, "theme": theme, "user": current_user}
    )

@router.post("/asset-categories/{category_id}/edit")
async def edit_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    name: Annotated[str, Form(...)],
    description: Annotated[Optional[str], Form()] = None
):
    category = db.query(model.AssetCategory).filter(model.AssetCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    category.name = name
    category.description = description
    db.add(category)
    db.commit()
    return RedirectResponse(url="/asset-categories", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/asset-categories/{category_id}")
async def delete_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    category = db.query(model.AssetCategory).filter(model.AssetCategory.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)



# ASSIGNMENT & MAINTENANCE
# ==========================================

@router.post("/assets/{asset_id}/assign")
async def assign_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    employee_id: Annotated[Optional[int], Form()] = None,
    org_unit_id: Annotated[Optional[int], Form()] = None
):
    if not employee_id and not org_unit_id:
        raise HTTPException(status_code=400, detail="Must provide either employee_id or org_unit_id")
    service.assign_asset(db, asset_id, employee_id=employee_id, org_unit_id=org_unit_id, user_id=current_user.id)
    return RedirectResponse(url=f"/assets/{asset_id}/view", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assets/{asset_id}/return")
async def return_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.return_asset(db, asset_id, user_id=current_user.id)
    return RedirectResponse(url=f"/assets/{asset_id}/view", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assets/{asset_id}/maintenance")
async def schedule_maintenance(
    asset_id: int,
    scheduled_date: Annotated[date, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    cost: Annotated[Optional[float], Form()] = None,
    description: Annotated[Optional[str], Form()] = None
):
    maintenance_in = schema.AssetMaintenanceCreate(
        asset_id=asset_id,
        scheduled_date=scheduled_date,
        cost=cost,
        description=description
    )
    service.schedule_maintenance(db, asset_id, maintenance_in, user_id=current_user.id)
    return RedirectResponse(url=f"/assets/{asset_id}/view", status_code=status.HTTP_303_SEE_OTHER)

# ==========================================
# COMPONENTS
# ==========================================

@router.post("/assets/{asset_id}/components/add")
async def add_component(
    asset_id: int,
    component_id: Annotated[int, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    parent = service.get_asset(db, asset_id)
    component = service.get_asset(db, component_id)
    if parent and component and component.asset_type in [schema.AssetTypeEnum.COMPONENT, schema.AssetTypeEnum.ACCESSORY]:
        component.parent_asset_id = asset_id
        component.status = parent.status
        db.add(component)
        db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}/view", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assets/{asset_id}/components/{component_id}/remove")
async def remove_component(
    asset_id: int,
    component_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    component = service.get_asset(db, component_id)
    if component and component.parent_asset_id == asset_id:
        component.parent_asset_id = None
        component.status = schema.AssetStatusEnum.AVAILABLE
        db.add(component)
        db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}/view", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assets/{asset_id}/assign-parent")
async def assign_parent_asset(
    asset_id: int,
    parent_asset_id: Annotated[int, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    child = service.get_asset(db, asset_id)
    parent = service.get_asset(db, parent_asset_id)
    if child and parent and child.asset_type in [schema.AssetTypeEnum.COMPONENT, schema.AssetTypeEnum.ACCESSORY]:
        child.parent_asset_id = parent_asset_id
        child.status = parent.status
        db.add(child)
        db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}/view", status_code=status.HTTP_303_SEE_OTHER)

# ==========================================
# ASSET REQUESTS
# ==========================================

@router.get("/assets/requests", response_class=HTMLResponse)
async def list_asset_requests(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    skip: int = 0,
    limit: int = 100
):
    requests = service.get_requests(db, skip=skip, limit=limit)
    available_assets = db.query(model.Asset).filter(model.Asset.status == schema.AssetStatusEnum.AVAILABLE).all()
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/asset_requests.html",
        context={"requests": requests, "available_assets": available_assets, "theme": theme, "user": current_user}
    )

@router.get("/assets/my-requests", response_class=HTMLResponse)
async def list_my_asset_requests(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    employee = current_user.employee
    requests = []
    if employee:
        requests = service.get_employee_requests(db, employee.id)
        
    categories = service.get_categories(db, limit=100)
    employees = employee_service.get_employees(db, limit=1000)
    from app.modules.department.model import OrgUnit
    org_units = db.query(OrgUnit).all()
    
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="asset_mgmt/templates/my_asset_requests.html",
        context={"requests": requests, "categories": categories, "employees": employees, "org_units": org_units, "theme": theme, "user": current_user}
    )

@router.post("/assets/requests")
async def create_asset_request(
    category_id: Annotated[int, Form(...)],
    reason: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    target_type: Annotated[str, Form()] = "self",
    target_employee_id: Annotated[Optional[int], Form()] = None,
    target_org_unit_id: Annotated[Optional[int], Form()] = None
):
    employee = current_user.employee
    if not employee:
        raise HTTPException(status_code=400, detail="User is not linked to an employee profile")
    
    final_target_emp = None
    final_target_org = None
    if target_type == "other":
        final_target_emp = target_employee_id
    elif target_type == "org":
        final_target_org = target_org_unit_id
    
    request_in = schema.AssetRequestCreate(
        asset_category_id=category_id, 
        reason=reason,
        target_employee_id=final_target_emp,
        target_org_unit_id=final_target_org
    )
    service.create_request(db, employee.id, request_in)
    return RedirectResponse(url="/assets/my-requests", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assets/requests/{request_id}/approve")
async def approve_request(
    request_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    asset_id: Annotated[Optional[int], Form()] = None
):
    db_req = db.query(model.AssetRequest).filter(model.AssetRequest.id == request_id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Request not found")

    target_asset_id = db_req.asset_id or asset_id

    if target_asset_id:
        asset = service.get_asset(db, target_asset_id)
        if asset and asset.status == schema.AssetStatusEnum.AVAILABLE:
            assign_employee_id = db_req.target_employee_id or (db_req.employee_id if not db_req.target_org_unit_id else None)
            assign_org_unit_id = db_req.target_org_unit_id
            
            service.assign_asset(
                db, 
                target_asset_id, 
                employee_id=assign_employee_id, 
                org_unit_id=assign_org_unit_id, 
                user_id=current_user.id
            )
            if not db_req.asset_id:
                db_req.asset_id = target_asset_id

    service.update_request_status(db, request_id, schema.RequestStatusEnum.APPROVED, user_id=current_user.id)
    return RedirectResponse(url="/assets/requests", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/assets/requests/{request_id}/reject")
async def reject_request(
    request_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.update_request_status(db, request_id, schema.RequestStatusEnum.REJECTED, user_id=current_user.id)
    return RedirectResponse(url="/assets/requests", status_code=status.HTTP_303_SEE_OTHER)

# ==========================================
# REST API ENDPOINTS
# ==========================================

@router.get("/api/assets/{asset_id}/history", response_model=List[schema.AssetHistoryOut])
async def api_get_asset_history(asset_id: int, db: Annotated[Session, Depends(get_db)]):
    return service.get_asset_history(db, asset_id)

@router.get("/api/assets/bulk/templates")
async def api_get_bulk_templates():
    return {"message": "Template download URL here"}

@router.post("/api/assets/bulk", response_model=schema.BulkJobOut)
async def api_create_bulk_job(db: Annotated[Session, Depends(get_db)]):
    return service.create_bulk_job(db, job_type="IMPORT")

@router.get("/api/assets/bulk/jobs/{job_id}", response_model=schema.BulkJobOut)
async def api_get_bulk_job(job_id: int, db: Annotated[Session, Depends(get_db)]):
    job = service.get_bulk_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/api/assets/bulk")
async def api_delete_bulk(request: schema.BulkDeleteRequest, db: Annotated[Session, Depends(get_db)]):
    count = service.delete_assets_bulk(db, request.asset_ids)
    return {"deleted": count}

@router.get("/api/assets/export")
async def api_export_assets():
    return {"message": "Export download URL here"}

@router.post("/api/assets/{asset_id}/transfer")
async def api_transfer_asset(
    asset_id: int,
    request: schema.TransferRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.transfer_asset(db, asset_id, request.new_employee_id, request.new_org_unit_id, current_user.id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset transferred"}

@router.get("/api/assets/{asset_id}/custody", response_model=List[schema.AssetAssignmentOut])
async def api_get_asset_custody(asset_id: int, db: Annotated[Session, Depends(get_db)]):
    return service.get_asset_custody(db, asset_id)

@router.patch("/api/assets/requests/{request_id}/approval")
async def api_update_request_approval(
    request_id: int,
    request: schema.ApprovalRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    req = service.update_request_status(db, request_id, request.status, current_user.id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"message": f"Request status updated to {request.status.value}"}

@router.post("/api/assets/requests/{request_id}/transit")
async def api_request_transit(
    request_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    req = service.update_request_status(db, request_id, schema.RequestStatusEnum.IN_TRANSIT, current_user.id)
    return {"message": "Request moved to transit"}

@router.post("/api/assets/requests/{request_id}/confirmation")
async def api_request_confirmation(
    request_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    req = service.update_request_status(db, request_id, schema.RequestStatusEnum.COMPLETED, current_user.id)
    return {"message": "Request completed"}

@router.post("/api/assets/requests/{request_id}/cancel")
async def api_request_cancel(
    request_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    req = service.update_request_status(db, request_id, schema.RequestStatusEnum.CANCELLED, current_user.id)
    return {"message": "Request cancelled"}

@router.patch("/api/assets/{asset_id}/status")
async def api_update_asset_status(
    asset_id: int,
    status: schema.AssetStatusEnum,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.update_asset_status(db, asset_id, status, current_user.id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": f"Status updated to {status.value}"}

@router.post("/api/assets/{asset_id}/report-issue")
async def api_report_issue(
    asset_id: int,
    report: schema.AssetIssueReport,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    employee_id = current_user.employee.id if current_user.employee else 1
    asset = service.report_issue(db, asset_id, report.description, employee_id, current_user.id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Issue reported"}

@router.post("/api/assets/{asset_id}/lost-stolen")
async def api_report_lost_stolen(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.update_asset_status(db, asset_id, schema.AssetStatusEnum.LOST, current_user.id)
    return {"message": "Asset reported lost/stolen"}

@router.post("/api/assets/{asset_id}/audit")
async def api_audit_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.audit_asset(db, asset_id, current_user.id)
    return {"message": "Asset audited"}

@router.get("/api/assets/{asset_id}/depreciation", response_model=schema.DepreciationResponse)
async def api_get_depreciation(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    return service.calculate_depreciation(db, asset_id)

@router.post("/api/assets/{asset_id}/dispose")
async def api_dispose_asset(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.dispose_asset(db, asset_id, current_user.id)
    return {"message": "Asset disposed"}


@router.patch("/api/assets/{asset_id}/licenses/seats")
async def api_update_licenses(
    asset_id: int,
    update: schema.LicensesUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.update_licenses(db, asset_id, update.consumed_seats, current_user.id)
    return {"message": "Licenses updated"}

@router.post("/api/assets/consumables/reorder")
async def api_reorder_consumables(
    asset_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    asset = service.reorder_consumables(db, asset_id, current_user.id)
    return {"message": "Consumables reordered"}
