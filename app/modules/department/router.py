from typing import Annotated, Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.department import service, schema, model
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_org_units(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    org_units = service.get_org_units(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="department/templates/department.html",
        context={"org_units": org_units, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_org_unit_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    org_units = service.get_org_units(db)
    return templates.TemplateResponse(
        request=request,
        name="department/templates/create-department.html",
        context={
            "theme": theme, 
            "user": current_user, 
            "org_units": org_units,
            "unit_types": model.OrgUnitType
        }
    )

@router.post("/create")
async def create_org_unit(
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None,
    unit_type: Annotated[model.OrgUnitType, Form()] = model.OrgUnitType.DEPARTMENT,
    parent_id: Annotated[Optional[int], Form()] = None
):
    org_unit_in = schema.OrgUnitCreate(
        name=name, 
        description=description, 
        unit_type=unit_type,
        parent_id=parent_id
    )
    service.create_org_unit(db, org_unit_in)
    return RedirectResponse(url="/department/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{org_unit_id}/edit", response_class=HTMLResponse)
async def edit_org_unit_page(
    org_unit_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    org_unit = service.get_org_unit(db, org_unit_id)
    if not org_unit:
        raise HTTPException(status_code=404, detail="OrgUnit not found")
    
    org_units = service.get_org_units(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="department/templates/edit-department.html",
        context={
            "org_unit": org_unit, 
            "org_units": org_units,
            "theme": theme, 
            "user": current_user,
            "unit_types": model.OrgUnitType
        }
    )

@router.post("/{org_unit_id}/edit")
async def edit_org_unit(
    org_unit_id: int,
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None,
    unit_type: Annotated[model.OrgUnitType, Form()] = model.OrgUnitType.DEPARTMENT,
    parent_id: Annotated[Optional[int], Form()] = None
):
    org_unit_in = schema.OrgUnitUpdate(
        name=name, 
        description=description,
        unit_type=unit_type,
        parent_id=parent_id
    )
    service.update_org_unit(db, org_unit_id, org_unit_in)
    return RedirectResponse(url="/department/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{org_unit_id}")
async def delete_org_unit(
    org_unit_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_org_unit(db, org_unit_id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
