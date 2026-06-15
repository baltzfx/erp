from typing import Optional, Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.department import service, schema
from app.api import deps
from app.modules.users.model import User

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_departments(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    departments = service.get_departments(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="department/templates/department.html",
        context={"departments": departments, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_department_page(
    request: Request,
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="department/templates/create-department.html",
        context={"theme": theme, "user": current_user}
    )

@router.post("/create")
async def create_department(
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    department_in = schema.DepartmentCreate(name=name, description=description)
    service.create_department(db, department_in)
    return RedirectResponse(url="/department/", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{department_id}/edit", response_class=HTMLResponse)
async def edit_department_page(
    department_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    department = service.get_department(db, department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="department/templates/edit-department.html",
        context={"department": department, "theme": theme, "user": current_user}
    )

@router.post("/{department_id}/edit")
async def edit_department(
    department_id: int,
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None
):
    department_in = schema.DepartmentUpdate(name=name, description=description)
    service.update_department(db, department_id, department_in)
    return RedirectResponse(url="/department/", status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_department(db, department_id)
    return HTMLResponse(content="", status_code=status.HTTP_200_OK)
