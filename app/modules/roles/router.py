from typing import List, Optional, Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.modules.roles import service, schema
from app.api import deps
from app.modules.users.model import User
from app.modules.permissions import service as permission_service

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def list_roles(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    roles = service.get_roles(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="roles/templates/roles.html",
        context={"roles": roles, "theme": theme, "user": current_user}
    )

@router.get("/create", response_class=HTMLResponse)
async def create_role_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    permissions = permission_service.get_permissions(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="roles/templates/create-role.html",
        context={"theme": theme, "user": current_user, "permissions": permissions}
    )

@router.post("/create")
async def create_role(
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None,
    permission_ids: Annotated[List[int], Form()] = []
):
    role_in = schema.RoleCreate(name=name, description=description, permission_ids=permission_ids)
    service.create_role(db, role_in)
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/roles/"}
    )

@router.get("/{role_id}/edit", response_class=HTMLResponse)
async def edit_role_page(
    role_id: int,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    role = service.get_role(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permissions = permission_service.get_permissions(db)
    theme = request.cookies.get("theme", "light")
    return templates.TemplateResponse(
        request=request,
        name="roles/templates/edit-role.html",
        context={"role": role, "theme": theme, "user": current_user, "permissions": permissions}
    )

@router.post("/{role_id}/edit")
async def edit_role(
    role_id: int,
    name: Annotated[str, Form(...)],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)],
    description: Annotated[Optional[str], Form()] = None,
    permission_ids: Annotated[List[int], Form()] = []
):
    role_in = schema.RoleUpdate(name=name, description=description, permission_ids=permission_ids)
    service.update_role(db, role_id, role_in)
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/roles/"}
    )

@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(deps.get_current_user)]
):
    service.delete_role(db, role_id)
    return JSONResponse(
        content={"status": "success"},
        headers={"HX-Redirect": "/roles/"}
    )
